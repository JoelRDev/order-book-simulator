# pragma once

# include "market_data.h"

# include <cstdint>
# include <fstream>
# include <optional>
# include <string>

class TradeReader {
public:
    explicit TradeReader(const std::string& path);
    bool next(Trade& trade);

private:
    std::ifstream file_;
    std::int64_t last_recv_time_ns_{};
};

struct BookRow {
    std::int64_t recv_time_ns{};
    std::int64_t event_time_ms{};
    std::int64_t update_id{};
    bool is_bid{};
    std::int64_t level{};
    PriceLevel price_level;
};

class BookReader {
public:
    explicit BookReader(const std::string& path);
    bool next(MarketSnapshot& snapshot);

private:
    bool read_row(BookRow& row);

    std::ifstream file_;
    std::optional<BookRow> pending_; // First row of the next snapshot, read ahead while finishing the current one
    std::int64_t last_recv_time_ns_{};
};
