#include "csv_reader.h"
#include "market_data.h"

#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>

constexpr double SCALE = 100'000'000.0;
constexpr int EVENTS_TO_PRINT = 20;

double display_e8(std::int64_t value) {
    return static_cast<double>(value) / SCALE;
};

void print_snapshot(const MarketSnapshot& snapshot) {
    const PriceLevel& best_bid = snapshot.bids.front();
    const PriceLevel& best_ask = snapshot.asks.front();
    std::cout
        << "BOOK  " << snapshot.recv_time_ns
        << "  bid " << display_e8(best_bid.price_e8) << " x " << display_e8(best_bid.quantity_e8)
        << "  ask " << display_e8(best_ask.price_e8) << " x " << display_e8(best_ask.quantity_e8)
        << '\n';
}

void print_trade(const Trade& trade) {
    std::cout
        << "TRADE " << trade.recv_time_ns
        << "  " << (trade.is_buyer_maker ? "SELL" : "BUY ")
        << ' ' << display_e8(trade.quantity_e8) << " @ " << display_e8(trade.price_e8)
        << '\n';
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: stage1_replay <book.csv> <trades.csv>\n";
        return 1;
    }

    try {
        BookReader books{argv[1]};
        TradeReader trades{argv[2]};

        MarketSnapshot snapshot;
        Trade trade;
        bool has_snapshot = books.next(snapshot);
        bool has_trade = trades.next(trade);

        std::int64_t snapshot_count = 0;
        std::int64_t trade_count = 0;

        std::cout << std::fixed << std::setprecision(4);

        // Merge the two time-ordered streams: always handle whichever event arrived first
        while (has_snapshot || has_trade) {
            const bool print = snapshot_count + trade_count < EVENTS_TO_PRINT;
            if (has_snapshot && (!has_trade || snapshot.recv_time_ns < trade.recv_time_ns)) {
                if (print) {
                    print_snapshot(snapshot);
                }
                ++snapshot_count;
                has_snapshot = books.next(snapshot);
            } else {
                if (print) {
                    print_trade(trade);
                }
                ++trade_count;
                has_trade = trades.next(trade);
            }
        }

        std::cout
            << "...\n"
            << "Snapshots: " << snapshot_count << '\n'
            << "Trades: " << trade_count << '\n';
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
