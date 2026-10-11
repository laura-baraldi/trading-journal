"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { supabase } from "../../lib/supabase";
import { API_URL } from "../../lib/api";
import Sidebar from "../../components/Sidebar";
import TradesTable from "../../components/TradesTable";
import DateRangeFilter, { type DateRangePreset } from "../../components/DateRangeFilter";
import type { Trade } from "../../types/trade";

type PaginatedTradesResponse = {
    items: Trade[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
};

type Account = {
    id: number;
    user_id: string;
    name: string;
    starting_balance: number;
    currency: string;
    broker: string | null;
    account_type: string | null;
    created_at?: string;
};

function formatDate(date: Date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

function TradesPageContent() {
    const searchParams = useSearchParams();
    const router = useRouter();

    const accountIdParam = searchParams.get("account_id");
    const accountIdFromUrl = accountIdParam !== null ? Number(accountIdParam) : null;

    const [trades, setTrades] = useState<Trade[]>([]);
    const [accounts, setAccounts] = useState<Account[]>([]);
    const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(0);
    const [editingTradeId, setEditingTradeId] = useState<number | null>(null);
    const [datePreset, setDatePreset] = useState<DateRangePreset>("all");
    const [dateFrom, setDateFrom] = useState("");
    const [dateTo, setDateTo] = useState("");

    const [symbol, setSymbol] = useState("");
    const [direction, setDirection] = useState("");
    const [entry, setEntry] = useState("");
    const [stop, setStop] = useState("");
    const [exit, setExit] = useState("");
    const [pnl, setPnl] = useState("");
    const [entryDatetime, setEntryDatetime] = useState("");
    const [exitDatetime, setExitDatetime] = useState("");

    const [tradesError, setTradesError] = useState<string | null>(null);
    const [tradeError, setTradeError] = useState<string | null>(null);
    const [userEmail, setUserEmail] = useState<string | null>(null);
    const [authLoading, setAuthLoading] = useState(true);

    const loadTrades = useCallback(async (accountId: number, page: number) => {
        const incompleteCustomRange = datePreset === "custom" && (!dateFrom || !dateTo);
        const invalidCustomRange = datePreset === "custom" && dateFrom > dateTo;

        if (incompleteCustomRange || invalidCustomRange) return;

        const {
            data: { session },
        } = await supabase.auth.getSession();

        if (!session) {
            router.push("/login");
            return;
        }

        const params = new URLSearchParams({
            account_id: String(accountId),
            page: String(page),
            page_size: "20",
        });

        if (dateFrom) params.set("date_from", dateFrom);
        if (dateTo) params.set("date_to", dateTo);

        const response = await fetch(`${API_URL}/trades?${params}`, {
            cache: "no-store",
            headers: {
                Authorization: `Bearer ${session.access_token}`,
            },
        });

        if (!response.ok) {
            setTradesError("Unable to load trades.");
            setAuthLoading(false);
            return;
        }

        const data: PaginatedTradesResponse = await response.json();

        setTrades(data.items);
        setTotalPages(data.total_pages);
        setTradesError(null);
        setAuthLoading(false);
    }, [dateFrom, datePreset, dateTo, router]);

    function handleDatePresetChange(preset: DateRangePreset) {
        setDatePreset(preset);
        setCurrentPage(1);

        if (preset === "all") {
            setDateFrom("");
            setDateTo("");
            return;
        }

        if (preset === "custom") return;

        const today = new Date();
        const firstDay = new Date(today);

        firstDay.setDate(today.getDate() - (preset === "30d" ? 29 : 89));

        setDateFrom(formatDate(firstDay));
        setDateTo(formatDate(today));
    }

    function handleDateFromChange(value: string) {
        setCurrentPage(1);
        setDateFrom(value);
    }

    function handleDateToChange(value: string) {
        setCurrentPage(1);
        setDateTo(value);
    }

    async function handleLogout() {
        await supabase.auth.signOut();
        router.push("/login");
    }

    function handleEditTrade(trade: Trade) {
        setEditingTradeId(trade.id);
        setSymbol(trade.symbol);
        setDirection(trade.direction);
        setEntry(String(trade.entry));
        setStop(trade.stop === null ? "" : String(trade.stop));
        setExit(String(trade.exit));
        setPnl(String(trade.pnl));
        setEntryDatetime(trade.entry_datetime.slice(0, 16));
        setExitDatetime(trade.exit_datetime.slice(0, 16));
    }

    async function handleUpdateTrade(tradeId: number) {
        if (!entryDatetime || !exitDatetime) {
            setTradeError("Both entry and exit dates are required.");
            return;
        }

        if (new Date(exitDatetime) < new Date(entryDatetime)) {
                setTradeError("Exit date cannot be before entry date.");
                return;
        }
                
        const {
            data: { session },
        } = await supabase.auth.getSession();

        if (!session) {
            router.push("/login");
            return;
        }

        const response = await fetch(`${API_URL}/trades/${tradeId}`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${session.access_token}`,
            },
            body: JSON.stringify({
                symbol,
                direction,
                entry: Number(entry),
                stop: stop === "" ? null : Number(stop),
                exit: Number(exit),
                pnl: Number(pnl),
                entry_datetime: entryDatetime,
                exit_datetime: exitDatetime,
            }),
        });

        if (response.ok) {
            if (selectedAccountId !== null) {
                await loadTrades(selectedAccountId, currentPage);
            }

            setEditingTradeId(null);
        }
    }

    async function handleDeleteTrade(tradeId: number) {
        const {
            data: { session },
        } = await supabase.auth.getSession();

        if (!session) {
            router.push("/login");
            return;
        }

        const response = await fetch(`${API_URL}/trades/${tradeId}`, {
            method: "DELETE",
            headers: {
                Authorization: `Bearer ${session.access_token}`,
            },
        });

        if (response.ok && selectedAccountId !== null) {
            if (trades.length === 1 && currentPage > 1) {
                setCurrentPage((page) => page - 1);
            } else {
                await loadTrades(selectedAccountId, currentPage);
            }
        }
    }

    useEffect(() => {
        async function fetchAccounts() {
            const {
                data: { session },
            } = await supabase.auth.getSession();

            if (!session) {
                router.push("/login");
                return;
            }

            setUserEmail(session.user.email ?? null);

            const response = await fetch(`${API_URL}/accounts`, {
                cache: "no-store",
                headers: {
                    Authorization: `Bearer ${session.access_token}`,
                },
            });

            if (!response.ok) {
                setAuthLoading(false);
                return;
            }

            const data: Account[] = await response.json();

            setAccounts(data);

            if (data.length === 0) {
                setTrades([]);
                setTotalPages(0);
                setSelectedAccountId(null);
                setAuthLoading(false);
                return;
            }

            const accountFromUrl = data.find(
                (account) => account.id === accountIdFromUrl,
            );

            setCurrentPage(1);
            setSelectedAccountId(accountFromUrl ? accountFromUrl.id : data[0].id);
        }

        fetchAccounts();
    }, [accountIdFromUrl, router]);

    useEffect(() => {
        if (selectedAccountId === null) return;

        async function fetchTrades() {
            await loadTrades(selectedAccountId!, currentPage);
        }

        fetchTrades();
    }, [selectedAccountId, currentPage, loadTrades]);

    const visiblePageCount = Math.min(5, totalPages);
    const firstVisiblePage = Math.max(1, Math.min(currentPage - 2, totalPages - 4));

    const visiblePages = Array.from(
        { length: visiblePageCount },
        (_, index) => firstVisiblePage + index,
    );

    if (authLoading) return null;

    return (
        <div className="flex min-h-screen bg-slate-50">
            <Sidebar userEmail={userEmail} onLogout={handleLogout} />

            <main className="min-w-0 flex-1 px-5 py-5 sm:px-6 md:px-8 md:py-8 xl:px-10">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                    <div className="pl-14 md:pl-0">
                        <h2 className="text-3xl font-bold tracking-tight text-slate-900">
                            Trades
                        </h2>

                        <p className="mt-1 text-sm text-slate-500">
                            Review and manage your trading history.
                        </p>
                    </div>

                    <div className="w-full sm:w-64">
                        <label
                            htmlFor="account-select"
                            className="mb-1 block text-sm font-medium text-slate-700"
                        >
                            Account
                        </label>

                        <select
                            id="account-select"
                            value={selectedAccountId ?? ""}
                            onChange={(event) => {
                                setCurrentPage(1);
                                setSelectedAccountId(Number(event.target.value));
                            }}
                            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                        >
                            {accounts.map((account) => (
                                <option key={account.id} value={account.id}>
                                    {account.name}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                <DateRangeFilter
                    preset={datePreset}
                    dateFrom={dateFrom}
                    dateTo={dateTo}
                    onPresetChange={handleDatePresetChange}
                    onDateFromChange={handleDateFromChange}
                    onDateToChange={handleDateToChange}
                />

                {tradesError && (
                    <p className="mt-4 text-sm font-medium text-red-600">
                        {tradesError}
                    </p>
                )}

                <TradesTable
                    trades={trades}
                    editingTradeId={editingTradeId}
                    symbol={symbol}
                    direction={direction}
                    entry={entry}
                    stop={stop}
                    exit={exit}
                    pnl={pnl}
                    entryDatetime={entryDatetime}
                    exitDatetime={exitDatetime}
                    setSymbol={setSymbol}
                    setDirection={setDirection}
                    setEntry={setEntry}
                    setStop={setStop}
                    setExit={setExit}
                    setPnl={setPnl}
                    setEntryDatetime={setEntryDatetime}
                    setExitDatetime={setExitDatetime}
                    onEdit={handleEditTrade}
                    onUpdate={handleUpdateTrade}
                    onDelete={handleDeleteTrade}
                />

                {totalPages > 1 && (
                    <div className="mt-6 flex items-center justify-center gap-2">
                        <button
                            type="button"
                            onClick={() => setCurrentPage((page) => page - 1)}
                            disabled={currentPage === 1}
                            className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-40"
                        >
                            ←
                        </button>

                        {visiblePages.map((pageNumber) => (
                            <button
                                key={pageNumber}
                                type="button"
                                onClick={() => setCurrentPage(pageNumber)}
                                className={
                                    currentPage === pageNumber
                                        ? "h-9 min-w-9 rounded-lg bg-blue-600 px-3 text-sm font-semibold text-white"
                                        : "h-9 min-w-9 rounded-lg border border-slate-200 bg-white px-3 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
                                }
                            >
                                {pageNumber}
                            </button>
                        ))}

                        <button
                            type="button"
                            onClick={() => setCurrentPage((page) => page + 1)}
                            disabled={currentPage === totalPages}
                            className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-40"
                        >
                            →
                        </button>
                    </div>
                )}

            </main>

            {tradeError && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
                    <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
                        <h3 className="text-xl font-bold text-rose-600">
                            Invalid trade
                        </h3>

                        <p className="mt-3 text-sm leading-6 text-zinc-700">
                            {tradeError}
                        </p>

                        <div className="mt-6 flex justify-end">
                            <button
                                type="button"
                                onClick={() => setTradeError(null)}
                                className="cursor-pointer rounded-lg bg-black px-4 py-2 text-sm font-semibold text-white transition hover:bg-zinc-800"
                            >
                                OK
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}


export default function TradesPage() {
    return (
        <Suspense fallback={null}>
            <TradesPageContent />
        </Suspense>
    );
}