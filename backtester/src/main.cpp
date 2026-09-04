#include "market_data.h"

#include <cstdint>
#include <iomanip>
#include <iostream>

constexpr double SCALE = 100'000'000.0;

double display_e8(std::int64_t value) {
    return static_cast<double>(value) / SCALE;
};

int main() {
    MarketSnapshot snapshot{
        .event_time_ms = 1'788'416'655'210,
        .update_id = 11'461'792'308'353,
        .bids = {
            PriceLevel{
                .price_e8 = 7'774'050'000'000,
                .quantity_e8 = 594'500'000,
            },
            PriceLevel{
                .price_e8 = 7'774'040'000'000,
                .quantity_e8 = 51'400'000
            },
        },
        .asks = {
            PriceLevel{
                .price_e8 = 7'774'060'000'000,
                .quantity_e8 = 601'500'000,
            },
            PriceLevel{
                .price_e8 = 7'774'070'000'000,
                .quantity_e8 = 3'100'000,
            },
        },
    };
    const PriceLevel& best_bid = snapshot.bids.front();
    const PriceLevel& best_ask = snapshot.asks.front();

    const std::int64_t spread_e8 = best_ask.price_e8 - best_bid.price_e8;

    std::cout
        << std::fixed
        << std::setprecision(8)
        << "Update:" << snapshot.update_id << '\n'
        << "Bid levels:" << snapshot.bids.size() << '\n'
        << "Ask levels:" << snapshot.asks.size() << '\n'
        << "Best bid:" << display_e8(best_bid.price_e8) << '\n'
        << "Best ask:" << display_e8(best_ask.price_e8) << '\n'
        << "Spread:" << display_e8(spread_e8) << '\n';

    return 0;
}