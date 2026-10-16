#include "csv_reader.h"

#include <charconv>
#include <stdexcept>
#include <string_view>
#include <vector>

namespace {

constexpr std::string_view TRADE_HEADER =
    "recv_time_ns,event_time_ms,trade_time_ms,agg_trade_id,price_e8,quantity_e8,normal_quantity_e8,is_buyer_maker";
constexpr std::string_view BOOK_HEADER =
    "recv_time_ns,event_time_ms,update_id,side,level,price_e8,quantity_e8";

// Views point into `line`, so they are only valid while `line` is alive and unchanged
std::vector<std::string_view> split(std::string_view line, char delimiter) {
    std::vector<std::string_view> fields;
    std::size_t start = 0;
    while (true) {
        const std::size_t end = line.find(delimiter, start);
        if (end == std::string_view::npos) {
            fields.push_back(line.substr(start));
            return fields;
        }
        fields.push_back(line.substr(start, end - start));
        start = end + 1;
    }
}

std::int64_t parse_int64(std::string_view field) {
    std::int64_t value{};
    const char* last = field.data() + field.size();
    const auto [ptr, error] = std::from_chars(field.data(), last, value);
    if (error != std::errc{} || ptr != last) {
        throw std::runtime_error("Invalid integer: " + std::string{field});
    }
    return value;
}

bool parse_bool(std::string_view field) {
    if (field == "True") {
        return true;
    }
    if (field == "False") {
        return false;
    }
    throw std::runtime_error("Invalid bool: " + std::string{field});
}

// Opens the file and rejects it unless the header matches the column order the parser expects
std::ifstream open_csv(const std::string& path, std::string_view expected_header) {
    std::ifstream file{path};
    if (!file) {
        throw std::runtime_error("Could not open " + path);
    }
    std::string header;
    std::getline(file, header);
    if (header != expected_header) {
        throw std::runtime_error("Unexpected header in " + path + ": " + header);
    }
    return file;
}

void check_time_order(std::int64_t recv_time_ns, std::int64_t& last_recv_time_ns) {
    if (recv_time_ns <= last_recv_time_ns) {
        throw std::runtime_error("recv_time_ns went backwards: " + std::to_string(recv_time_ns));
    }
    last_recv_time_ns = recv_time_ns;
}

void add_level(MarketSnapshot& snapshot, const BookRow& row) {
    std::vector<PriceLevel>& levels = row.is_bid ? snapshot.bids : snapshot.asks;
    if (row.level != static_cast<std::int64_t>(levels.size())) {
        throw std::runtime_error("Out of order level in update " + std::to_string(row.update_id));
    }
    levels.push_back(row.price_level);
}

void validate(const MarketSnapshot& snapshot) {
    const std::string update = std::to_string(snapshot.update_id);
    if (snapshot.bids.empty() || snapshot.asks.empty()) {
        throw std::runtime_error("Empty side in update " + update);
    }
    for (std::size_t i = 1; i < snapshot.bids.size(); ++i) {
        if (snapshot.bids[i].price_e8 >= snapshot.bids[i - 1].price_e8) {
            throw std::runtime_error("Bids not descending in update " + update);
        }
    }
    for (std::size_t i = 1; i < snapshot.asks.size(); ++i) {
        if (snapshot.asks[i].price_e8 <= snapshot.asks[i - 1].price_e8) {
            throw std::runtime_error("Asks not ascending in update " + update);
        }
    }
    if (snapshot.bids.front().price_e8 >= snapshot.asks.front().price_e8) {
        throw std::runtime_error("Crossed book in update " + update);
    }
}

} // namespace

TradeReader::TradeReader(const std::string& path)
    : file_{open_csv(path, TRADE_HEADER)} {}

bool TradeReader::next(Trade& trade) {
    std::string line;
    if (!std::getline(file_, line)) {
        return false;
    }
    const std::vector<std::string_view> fields = split(line, ',');
    if (fields.size() != 8) {
        throw std::runtime_error("Expected 8 trade fields, got: " + line);
    }
    // Column positions are guaranteed by the header check in open_csv
    trade = Trade{
        .recv_time_ns = parse_int64(fields[0]),
        .event_time_ms = parse_int64(fields[1]),
        .trade_time_ms = parse_int64(fields[2]),
        .agg_trade_id = parse_int64(fields[3]),
        .price_e8 = parse_int64(fields[4]),
        .quantity_e8 = parse_int64(fields[5]),
        .normal_quantity_e8 = parse_int64(fields[6]),
        .is_buyer_maker = parse_bool(fields[7]),
    };
    check_time_order(trade.recv_time_ns, last_recv_time_ns_);
    return true;
}

BookReader::BookReader(const std::string& path)
    : file_{open_csv(path, BOOK_HEADER)} {}

bool BookReader::read_row(BookRow& row) {
    std::string line;
    if (!std::getline(file_, line)) {
        return false;
    }
    const std::vector<std::string_view> fields = split(line, ',');
    if (fields.size() != 7) {
        throw std::runtime_error("Expected 7 book fields, got: " + line);
    }
    if (fields[3] != "bid" && fields[3] != "ask") {
        throw std::runtime_error("Invalid side: " + line);
    }
    row = BookRow{
        .recv_time_ns = parse_int64(fields[0]),
        .event_time_ms = parse_int64(fields[1]),
        .update_id = parse_int64(fields[2]),
        .is_bid = fields[3] == "bid",
        .level = parse_int64(fields[4]),
        .price_level = PriceLevel{
            .price_e8 = parse_int64(fields[5]),
            .quantity_e8 = parse_int64(fields[6]),
        },
    };
    return true;
}

bool BookReader::next(MarketSnapshot& snapshot) {
    BookRow row;
    if (pending_) {
        row = *pending_;
        pending_.reset();
    } else if (!read_row(row)) {
        return false;
    }

    snapshot.recv_time_ns = row.recv_time_ns;
    snapshot.event_time_ms = row.event_time_ms;
    snapshot.update_id = row.update_id;
    snapshot.bids.clear(); // clear() keeps the allocated capacity, so later snapshots reuse the memory
    snapshot.asks.clear();
    add_level(snapshot, row);

    // Rows belong to this snapshot until update_id changes; that row is saved for the next call
    while (read_row(row)) {
        if (row.update_id != snapshot.update_id) {
            pending_ = row;
            break;
        }
        add_level(snapshot, row);
    }

    validate(snapshot);
    check_time_order(snapshot.recv_time_ns, last_recv_time_ns_);
    return true;
}
