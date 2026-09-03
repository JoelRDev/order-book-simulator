# pragma once

# include <cstdint>
# include <vector>

struct PriceLevel {
    std::int64_t price_e8{};
    std::int64_t quantity_e8{};
};

struct MarketSnapshot {
    std::int64_t event_time_ms{};
    std::int64_t update_id{};
    std::vector<PriceLevel> bids;
    std::vector<PriceLevel> asks;
};