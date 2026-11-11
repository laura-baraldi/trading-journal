
import os
import random

from datetime import datetime, timedelta, timezone
from supabase import create_client

from calculations import calculate_r
from database import (
    execute_query,
    supabase_key,
    supabase_url,
)


DEMO_ACCOUNT = {
    "name": "Demo Trading Account",
    "starting_balance": 100000,
    "currency": "USD",
    "broker": "Demo Broker",
    "account_type": "Personal Account",
}


# Synthetic market parameters for the demo dataset.
# Prices and trades are illustrative, not historical market data.
INSTRUMENTS = {
    "XAUUSD": {
        "base_price": 2650,
        "price_variation": 100,
        "risk_min": 8,
        "risk_max": 20,
        "precision": 2,
    },
    "EURUSD": {
        "base_price": 1.08,
        "price_variation": 0.04,
        "risk_min": 0.0015,
        "risk_max": 0.0040,
        "precision": 5,
    },
    "GBPUSD": {
        "base_price": 1.27,
        "price_variation": 0.05,
        "risk_min": 0.0020,
        "risk_max": 0.0050,
        "precision": 5,
    },
    "NAS100": {
        "base_price": 22000,
        "price_variation": 1500,
        "risk_min": 50,
        "risk_max": 120,
        "precision": 2,
    },
}


# R-multiple outcomes.
# Negative values represent losses, zero represents breakeven,
# and positive values represent profitable trades.
R_OUTCOMES = [
    -1.0,
    -1.0,
    -0.75,
    -0.5,
    0.0,
    0.5,
    0.75,
    1.0,
    1.25,
    1.5,
    2.0,
    2.5,
    3.0,
]

R_WEIGHTS = [
    12,
    10,
    5,
    4,
    8,
    8,
    8,
    12,
    10,
    8,
    6,
    4,
    3,
]


def build_demo_dataset():
    """Generate a deterministic set of 120 synthetic trading records."""

    rng = random.Random(42)

    total_trades = 120
    total_days = 180
    active_days = 80

    # Only weekdays are considered for trading activity.
    # Select 80 active days across the six-month period.
    available_days = [
        day
        for day in range(1, total_days + 1)
        if (
            datetime.now(timezone.utc).date()
            - timedelta(days=day)
        ).weekday() < 5
    ]

    selected_days = sorted(
        rng.sample(
            available_days,
            active_days,
        ),
        reverse=True,
    )

    # Forty days contain two trades and forty days contain one.
    daily_trade_counts = (
        [2] * 40
        + [1] * 40
    )

    rng.shuffle(daily_trade_counts)

    trades = []

    for days_ago, trades_today in zip(
        selected_days,
        daily_trade_counts,
    ):
        # Select distinct trading hours for each active day.
        available_hours = [
            8,
            9,
            10,
            11,
            13,
            14,
            15,
            16,
            17,
            18,
        ]

        trading_hours = sorted(
            rng.sample(
                available_hours,
                trades_today,
            )
        )

        for entry_hour in trading_hours:
            symbol = rng.choice(
                list(INSTRUMENTS.keys())
            )

            instrument = INSTRUMENTS[symbol]

            direction = rng.choice([
                "long",
                "short",
            ])

            # Generate an entry price around the instrument's
            # illustrative reference price.
            entry = (
                instrument["base_price"]
                + rng.uniform(
                    -instrument["price_variation"],
                    instrument["price_variation"],
                )
            )

            # Risk distance determines the stop-loss placement.
            risk_distance = rng.uniform(
                instrument["risk_min"],
                instrument["risk_max"],
            )

            if direction == "long":
                stop = entry - risk_distance
            else:
                stop = entry + risk_distance

            # Select an outcome from the predefined R distribution.
            target_r = rng.choices(
                R_OUTCOMES,
                weights=R_WEIGHTS,
                k=1,
            )[0]

            # Calculate the exit price from the desired R outcome.
            if direction == "long":
                exit_price = (
                    entry
                    + risk_distance * target_r
                )
            else:
                exit_price = (
                    entry
                    - risk_distance * target_r
                )

            precision = instrument["precision"]

            entry = round(entry, precision)
            stop = round(stop, precision)
            exit_price = round(
                exit_price,
                precision,
            )

            # Recalculate R from the rounded prices so that
            # the stored result matches the actual trade prices.
            result = round(
                calculate_r(
                    direction,
                    entry,
                    stop,
                    exit_price,
                ),
                2,
            )

            # Monetary risk varies between trades.
            # P&L is derived from the actual R result.
            risk_amount = rng.uniform(
                150,
                400,
            )

            pnl = round(
                result * risk_amount,
                2,
            )

            trades.append({
                "symbol": symbol,
                "direction": direction,
                "entry": entry,
                "stop": stop,
                "exit": exit_price,
                "pnl": pnl,
                "days_ago": days_ago,
                "entry_hour": entry_hour,
                "entry_minute": rng.choice([
                    0,
                    15,
                    30,
                    45,
                ]),
            })

    # Keep records in chronological order.
    trades.sort(
        key=lambda trade: (
            trade["days_ago"],
            trade["entry_hour"],
            trade["entry_minute"],
        ),
        reverse=True,
    )

    assert len(trades) == total_trades

    return trades


DEMO_TRADES = build_demo_dataset()


def get_demo_client():
    email = os.getenv("DEMO_EMAIL")
    password = os.getenv("DEMO_PASSWORD")

    if not email or not password:
        raise RuntimeError(
            "Demo account is not configured"
        )

    client = create_client(
        supabase_url,
        supabase_key,
    )

    response = (
        client.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
    )

    if not response.session or not response.user:
        raise RuntimeError(
            "Demo login failed"
        )

    client.postgrest.auth(
        response.session.access_token
    )

    return client, response.user.id


def build_demo_trades(
    account_id,
    user_id,
):
    now = datetime.now(
        timezone.utc
    ).replace(
        minute=0,
        second=0,
        microsecond=0,
    )

    trades = []

    for trade in DEMO_TRADES:
        entry_datetime = (
            now
            - timedelta(
                days=trade["days_ago"]
            )
            + timedelta(
                hours=trade["entry_hour"],
                minutes=trade["entry_minute"],
            )
        )

        exit_datetime = (
            entry_datetime
            + timedelta(hours=2)
        )

        result = round(
            calculate_r(
                trade["direction"],
                trade["entry"],
                trade["stop"],
                trade["exit"],
            ),
            2,
        )

        trades.append({
            "account_id": account_id,
            "user_id": user_id,
            "symbol": trade["symbol"],
            "direction": trade["direction"],
            "entry": trade["entry"],
            "stop": trade["stop"],
            "exit": trade["exit"],
            "result": result,
            "pnl": trade["pnl"],
            "entry_datetime":
                entry_datetime.isoformat(),
            "exit_datetime":
                exit_datetime.isoformat(),
        })

    return trades


def reset_demo_data():
    client, user_id = (
        get_demo_client()
    )

    execute_query(
        client
        .table("trades")
        .delete()
        .eq("user_id", user_id)
    )

    execute_query(
        client
        .table("accounts")
        .delete()
        .eq("user_id", user_id)
    )

    account = {
        **DEMO_ACCOUNT,
        "user_id": user_id,
    }

    account_response = execute_query(
        client
        .table("accounts")
        .insert(account)
    )

    account_id = (
        account_response
        .data[0]["id"]
    )

    trades = build_demo_trades(
        account_id,
        user_id,
    )

    execute_query(
        client
        .table("trades")
        .insert(trades)
    )


def should_reset_demo():
    client, user_id = get_demo_client()

    response = execute_query(
        client
        .table("demo_state")
        .select("last_activity_at")
        .eq("user_id", user_id)
        .single()
    )

    last_activity = datetime.fromisoformat(
        response.data["last_activity_at"]
        .replace("Z", "+00:00")
    )

    inactive_for = (
        datetime.now(timezone.utc)
        - last_activity
    )

    return inactive_for >= timedelta(
        minutes=30
    )


def reset_demo_if_inactive():
    force_reset = (
        os.getenv("FORCE_DEMO_RESET", "").lower()
        == "true"
    )

    if force_reset:
        print("Forced demo reset requested.")
        reset_demo_data()
        print("Demo data reset.")
        return

    if should_reset_demo():
        reset_demo_data()
        print("Demo data reset.")
    else:
        print("Demo is active. Reset skipped.")


if __name__ == "__main__":  # pragma: no cover
    reset_demo_if_inactive()
