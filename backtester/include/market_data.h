# pragma once

# include <cstdint>
# include <vector>

struct PriceLevel {
    std::int64_t price_e8{};
    std::int64_t quantity_e8{};
};

struct MarketSnapshot {
    std::int64_t recv_time_ns{};
    std::int64_t event_time_ms{};
    std::int64_t update_id{};
    std::vector<PriceLevel> bids;
    std::vector<PriceLevel> asks;
};

struct Trade {
    std::int64_t recv_time_ns{};
    std::int64_t event_time_ms{};
    std::int64_t trade_time_ms{};
    std::int64_t agg_trade_id{};
    std::int64_t price_e8{};
    std::int64_t quantity_e8{};
    std::int64_t normal_quantity_e8{};
    bool is_buyer_maker{}; // true -> seller was aggressor (trade hit the bid)
};
