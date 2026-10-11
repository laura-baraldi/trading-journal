import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import TradesPage from "./page";
import type { Trade } from "../../types/trade";

type Account = {
    id: number;
    user_id: string;
    name: string;
    starting_balance: number;
    currency: string;
    broker: string | null;
    account_type: string | null;
};

const {
    mockGetSession,
    mockSignOut,
    mockUseSearchParams,
    mockPush,
    mockRouter,
    tableCallbacks,
} = vi.hoisted(() => {
    const mockPush = vi.fn();

    return {
        mockGetSession: vi.fn(),
        mockSignOut: vi.fn(),
        mockUseSearchParams: vi.fn(),
        mockPush,
        mockRouter: {
            push: mockPush,
        },
        tableCallbacks: {
            onUpdate: null as ((tradeId: number) => void) | null,
            onDelete: null as ((tradeId: number) => void) | null,
        },
    };
});

vi.mock("../../lib/supabase", () => ({
    supabase: {
        auth: {
            getSession: mockGetSession,
            signOut: mockSignOut,
        },
    },
}));

vi.mock("next/navigation", () => ({
    useSearchParams: mockUseSearchParams,
    useRouter: () => mockRouter,
}));

vi.mock("../../components/Sidebar", () => ({
    default: ({
        userEmail,
        onLogout,
    }: {
        userEmail: string | null;
        onLogout: () => void;
    }) => (
        <div>
            <span data-testid="user-email">{userEmail ?? "no-email"}</span>
            <button type="button" onClick={onLogout}>Fake logout</button>
        </div>
    ),
}));

vi.mock("../../components/TradesTable", () => ({
    default: ({
        trades,
        onEdit,
        onUpdate,
        onDelete,
        editingTradeId,
        symbol,
        direction,
        entry,
        stop,
        exit,
        pnl,
        entryDatetime,
        exitDatetime,
    }: {
        trades: Trade[];
        onEdit: (trade: Trade) => void;
        onUpdate: (tradeId: number) => void;
        onDelete: (tradeId: number) => void;
        editingTradeId: number | null;
        symbol: string;
        direction: string;
        entry: string;
        stop: string;
        exit: string;
        pnl: string;
        entryDatetime: string;
        exitDatetime: string;
    }) => {
        tableCallbacks.onUpdate = onUpdate;
        tableCallbacks.onDelete = onDelete;

        return (
            <div>
                <span data-testid="trade-count">{trades.length}</span>

                <div data-testid="edit-state">
                    {symbol} | {direction} | {entry} | {stop} | {exit} | {pnl} | {entryDatetime} | {exitDatetime}
                </div>

                {trades.map((trade) => (
                    <div key={trade.id}>
                        <span>{trade.symbol}</span>

                        <button type="button" onClick={() => onEdit(trade)}>
                            Edit trade {trade.id}
                        </button>

                        <button type="button" onClick={() => onDelete(trade.id)}>
                            Delete trade {trade.id}
                        </button>
                    </div>
                ))}

                {editingTradeId !== null && (
                    <button type="button" onClick={() => onUpdate(editingTradeId)}>
                        Save trade
                    </button>
                )}
            </div>
        );
    },
}));

const fakeSession = {
    access_token: "fake-token",
    user: {
        email: "test@example.com",
    },
};

const fakeAccounts: Account[] = [
    {
        id: 7,
        user_id: "test-user",
        name: "FTMO 100K",
        starting_balance: 100000,
        currency: "USD",
        broker: "FTMO",
        account_type: "Prop Firm",
    },
];

let fetchMock: ReturnType<typeof vi.fn>;

function sessionResponse(session: {
    access_token: string;
    user: {
        email?: string;
    };
} | null = fakeSession) {
    return {
        data: {
            session,
        },
    };
}

function makeTrade({
    id = 1,
    symbol = "EURUSD",
    stop = 1.14,
    result = 2,
    entryDatetime = "2026-08-12T10:00",
    exitDatetime = "2026-08-12T11:00",
}: {
    id?: number;
    symbol?: string;
    stop?: number | null;
    result?: number | null;
    entryDatetime?: string;
    exitDatetime?: string;
} = {}): Trade {
    return {
        id,
        account_id: 7,
        symbol,
        direction: "long",
        entry: 1.15,
        stop,
        exit: 1.17,
        result,
        pnl: 250,
        entry_datetime: entryDatetime,
        exit_datetime: exitDatetime,
    };
}

function makeTrades(amount: number): Trade[] {
    return Array.from({ length: amount }, (_, index) =>
        makeTrade({
            id: index + 1,
            symbol: `TRADE-${index + 1}`,
        }),
    );
}

function response<T>(data: T, ok = true) {
    return {
        ok,
        json: async () => data,
    } as Response;
}

function accountsResponse(accounts: Account[] = fakeAccounts, ok = true) {
    return response(accounts, ok);
}

function tradesResponse(
    trades: Trade[] = [],
    ok = true,
    total = trades.length,
    page = 1,
    pageSize = 20,
) {
    return response({
        items: trades,
        page,
        page_size: pageSize,
        total,
        total_pages: Math.ceil(total / pageSize),
    }, ok);
}

function queueInitialLoad(trades: Trade[], accounts: Account[] = fakeAccounts) {
    fetchMock
        .mockResolvedValueOnce(accountsResponse(accounts))
        .mockResolvedValueOnce(tradesResponse(trades));
}

async function renderLoadedPage(trades: Trade[] = [makeTrade()], accounts: Account[] = fakeAccounts) {
    queueInitialLoad(trades, accounts);

    const renderResult = render(<TradesPage />);

    await waitFor(() => {
        expect(screen.getByTestId("trade-count")).toBeInTheDocument();
    });

    return renderResult;
}

async function clickEdit() {
    fireEvent.click(screen.getByRole("button", { name: "Edit trade 1" }));
}

async function movePageToNoAccounts(rerender: (ui: React.ReactNode) => void) {
    mockUseSearchParams.mockReturnValue(new URLSearchParams("account_id=999"));
    fetchMock.mockResolvedValueOnce(accountsResponse([]));

    rerender(<TradesPage />);

    await waitFor(() => {
        expect(screen.getByTestId("trade-count")).toHaveTextContent("0");
    });
}

describe("TradesPage", () => {
    beforeEach(() => {
        fetchMock = vi.fn();
        vi.stubGlobal("fetch", fetchMock);

        mockGetSession.mockReset();
        mockSignOut.mockReset();
        mockUseSearchParams.mockReset();
        mockPush.mockReset();

        tableCallbacks.onUpdate = null;
        tableCallbacks.onDelete = null;

        mockUseSearchParams.mockReturnValue(new URLSearchParams());
        mockGetSession.mockResolvedValue(sessionResponse());
        mockSignOut.mockResolvedValue(undefined);
    });

    afterEach(() => {
        cleanup();
        vi.restoreAllMocks();
        vi.unstubAllGlobals();
    });

    test("loads trades for the selected account", async () => {
        await renderLoadedPage();

        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/trades?account_id=7&page=1&page_size=20",
            expect.objectContaining({
                headers: expect.objectContaining({
                    Authorization: "Bearer fake-token",
                }),
            }),
        );
    });

    test("uses account id from URL", async () => {
        const accounts = [
            fakeAccounts[0],
            {
                ...fakeAccounts[0],
                id: 8,
                name: "Second account",
            },
        ];

        mockUseSearchParams.mockReturnValue(new URLSearchParams("account_id=8"));

        await renderLoadedPage([
            makeTrade({
                symbol: "GBPUSD",
            }),
        ], accounts);

        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/trades?account_id=8&page=1&page_size=20",
            expect.anything(),
        );
    });

    test("falls back to first account when URL account does not exist", async () => {
        mockUseSearchParams.mockReturnValue(new URLSearchParams("account_id=999"));

        await renderLoadedPage();

        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/trades?account_id=7&page=1&page_size=20",
            expect.anything(),
        );
    });

    test("loads another account from account selector", async () => {
        const accounts = [
            fakeAccounts[0],
            {
                ...fakeAccounts[0],
                id: 8,
                name: "Second account",
            },
        ];

        fetchMock
            .mockResolvedValueOnce(accountsResponse(accounts))
            .mockResolvedValueOnce(tradesResponse([makeTrade()]))
            .mockResolvedValueOnce(
                tradesResponse([
                    makeTrade({
                        id: 2,
                        symbol: "GBPUSD",
                    }),
                ]),
            );

        render(<TradesPage />);

        await screen.findByText("EURUSD");

        fireEvent.change(screen.getByLabelText("Account"), {
            target: {
                value: "8",
            },
        });

        expect(await screen.findByText("GBPUSD")).toBeInTheDocument();

        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/trades?account_id=8&page=1&page_size=20",
            expect.anything(),
        );
    });

    test("paginates trades 20 at a time", async () => {
        const firstPage = makeTrades(20);

        const secondPage = [
            makeTrade({
                id: 21,
                symbol: "TRADE-21",
            }),
        ];

        fetchMock
            .mockResolvedValueOnce(accountsResponse())
            .mockResolvedValueOnce(tradesResponse(firstPage, true, 21))
            .mockResolvedValueOnce(tradesResponse(secondPage, true, 21, 2))
            .mockResolvedValueOnce(tradesResponse(firstPage, true, 21))
            .mockResolvedValueOnce(tradesResponse(secondPage, true, 21, 2));

        render(<TradesPage />);

        await screen.findByText("TRADE-1");

        expect(screen.getByTestId("trade-count")).toHaveTextContent("20");
        expect(screen.queryByText("TRADE-21")).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole("button", { name: "2" }));

        expect(await screen.findByText("TRADE-21")).toBeInTheDocument();

        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/trades?account_id=7&page=2&page_size=20",
            expect.anything(),
        );

        fireEvent.click(screen.getByRole("button", { name: "←" }));

        expect(await screen.findByText("TRADE-1")).toBeInTheDocument();

        fireEvent.click(screen.getByRole("button", { name: "→" }));

        expect(await screen.findByText("TRADE-21")).toBeInTheDocument();
    });

    test("does not show pagination for one page", async () => {
        await renderLoadedPage();

        expect(
            screen.queryByRole("button", { name: "→" }),
        ).not.toBeInTheDocument();
    });

    test("uses null email when session has no email", async () => {
        mockGetSession.mockResolvedValue(
            sessionResponse({
                access_token: "fake-token",
                user: {},
            }),
        );

        await renderLoadedPage();

        expect(screen.getByTestId("user-email")).toHaveTextContent("no-email");
    });

    test("redirects when initial session is missing", async () => {
        mockGetSession.mockResolvedValue(sessionResponse(null));

        render(<TradesPage />);

        await waitFor(() => {
            expect(mockPush).toHaveBeenCalledWith("/login");
        });

        expect(fetchMock).not.toHaveBeenCalled();
    });

    test("redirects when session disappears while loading trades", async () => {
        mockGetSession
            .mockResolvedValueOnce(sessionResponse())
            .mockResolvedValueOnce(sessionResponse(null));

        fetchMock.mockResolvedValueOnce(accountsResponse());

        render(<TradesPage />);

        await waitFor(() => {
            expect(mockPush).toHaveBeenCalledWith("/login");
        });

        expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    test("shows an error when loading trades fails", async () => {
        fetchMock
            .mockResolvedValueOnce(accountsResponse())
            .mockResolvedValueOnce(tradesResponse([], false));

        render(<TradesPage />);

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledTimes(2);
        });

        expect(
            await screen.findByText("Unable to load trades."),
        ).toBeInTheDocument();

        expect(screen.getByTestId("trade-count")).toHaveTextContent("0");
    });

    test("shows page when account list is empty", async () => {
        fetchMock.mockResolvedValueOnce(accountsResponse([]));

        render(<TradesPage />);

        expect(
            await screen.findByRole("heading", { name: "Trades" }),
        ).toBeInTheDocument();

        expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    test("shows page when account request fails", async () => {
        fetchMock.mockResolvedValueOnce(accountsResponse([], false));

        render(<TradesPage />);

        expect(
            await screen.findByRole("heading", { name: "Trades" }),
        ).toBeInTheDocument();
    });

    test("loads trade values into edit state", async () => {
        await renderLoadedPage();
        await clickEdit();

        expect(screen.getByTestId("edit-state")).toHaveTextContent(
            "EURUSD | long | 1.15 | 1.14 | 1.17 | 250 | 2026-08-12T10:00 | 2026-08-12T11:00",
        );
    });

    test("updates trade without stop", async () => {
        const tradeWithoutStop = makeTrade({
            stop: null,
            result: null,
        });

        fetchMock
            .mockResolvedValueOnce(accountsResponse())
            .mockResolvedValueOnce(tradesResponse([tradeWithoutStop]))
            .mockResolvedValueOnce(tradesResponse())
            .mockResolvedValueOnce(tradesResponse([tradeWithoutStop]));

        render(<TradesPage />);

        await screen.findByText("EURUSD");
        await clickEdit();

        expect(screen.getByTestId("edit-state")).toHaveTextContent(
            "EURUSD | long | 1.15 | | 1.17 | 250 | 2026-08-12T10:00 | 2026-08-12T11:00",
        );

        fireEvent.click(screen.getByRole("button", { name: "Save trade" }));

        await waitFor(() => {
            const updateCall = fetchMock.mock.calls.find(
                ([url, options]) =>
                    url === "http://127.0.0.1:8000/trades/1"
                    && options?.method === "PATCH",
            );

            expect(
                JSON.parse(updateCall![1].body as string),
            ).toMatchObject({
                stop: null,
            });
        });
    });

    test("does not update when dates are missing", async () => {
        await renderLoadedPage([
            makeTrade({
                entryDatetime: "",
                exitDatetime: "",
            }),
        ]);

        await clickEdit();

        fireEvent.click(screen.getByRole("button", { name: "Save trade" }));
        expect(
            screen.getByText("Both entry and exit dates are required.")
        ).toBeInTheDocument();

        expect(fetchMock).toHaveBeenCalledTimes(2);
    });
        
    test("shows an error when updating a trade with reversed dates", async () => {
        const invalidTrade = makeTrade({
            entryDatetime: "2026-08-12T12:00",
            exitDatetime: "2026-08-12T10:00",
        });

        await renderLoadedPage([invalidTrade]);
        await clickEdit();

        fireEvent.click(screen.getByRole("button", { name: "Save trade" }));

        expect(
            screen.getByText("Exit date cannot be before entry date.")
        ).toBeInTheDocument();

        expect(
            fetchMock.mock.calls.some(
                ([url, options]) =>
                    String(url).endsWith("/trades/1") &&
                    options?.method === "PATCH"
            )
        ).toBe(false);

        fireEvent.click(screen.getByRole("button", { name: "OK" }));

        expect(
            screen.queryByText("Exit date cannot be before entry date.")
        ).not.toBeInTheDocument();
    });

    test("updates trade and reloads after success", async () => {
        const trade = makeTrade();

        fetchMock
            .mockResolvedValueOnce(accountsResponse())
            .mockResolvedValueOnce(tradesResponse([trade]))
            .mockResolvedValueOnce(tradesResponse())
            .mockResolvedValueOnce(tradesResponse([trade]));

        render(<TradesPage />);

        await screen.findByText("EURUSD");
        await clickEdit();

        fireEvent.click(screen.getByRole("button", { name: "Save trade" }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(
                "http://127.0.0.1:8000/trades/1",
                expect.objectContaining({
                    method: "PATCH",
                }),
            );
        });

        expect(fetchMock).toHaveBeenCalledTimes(4);
    });

    test("does not reload when update fails", async () => {
        fetchMock
            .mockResolvedValueOnce(accountsResponse())
            .mockResolvedValueOnce(tradesResponse([makeTrade()]))
            .mockResolvedValueOnce(tradesResponse([], false));

        render(<TradesPage />);

        await screen.findByText("EURUSD");
        await clickEdit();

        fireEvent.click(screen.getByRole("button", { name: "Save trade" }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledTimes(3);
        });
    });

    test("stops update when session is missing", async () => {
        mockGetSession
            .mockResolvedValueOnce(sessionResponse())
            .mockResolvedValueOnce(sessionResponse())
            .mockResolvedValueOnce(sessionResponse(null));

        await renderLoadedPage();
        await clickEdit();

        fireEvent.click(screen.getByRole("button", { name: "Save trade" }));

        await waitFor(() => {
            expect(mockPush).toHaveBeenCalledWith("/login");
        });

        expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    test("covers successful update when selected account becomes null", async () => {
        const { rerender } = await renderLoadedPage();

        await clickEdit();
        await movePageToNoAccounts(rerender);

        fetchMock.mockResolvedValueOnce(tradesResponse());

        expect(tableCallbacks.onUpdate).not.toBeNull();

        await act(async () => {
            await tableCallbacks.onUpdate!(1);
        });

        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/trades/1",
            expect.objectContaining({
                method: "PATCH",
            }),
        );

        expect(fetchMock).toHaveBeenCalledTimes(4);
    });

    test("deletes trade and reloads after success", async () => {
        fetchMock
            .mockResolvedValueOnce(accountsResponse())
            .mockResolvedValueOnce(tradesResponse([makeTrade()]))
            .mockResolvedValueOnce(tradesResponse())
            .mockResolvedValueOnce(tradesResponse());

        render(<TradesPage />);

        await screen.findByText("EURUSD");

        fireEvent.click(
            screen.getByRole("button", { name: "Delete trade 1" }),
        );

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(
                "http://127.0.0.1:8000/trades/1",
                expect.objectContaining({
                    method: "DELETE",
                }),
            );
        });

        expect(fetchMock).toHaveBeenCalledTimes(4);
    });

    test("moves to previous page after deleting the last trade", async () => {
        const firstPage = makeTrades(20);

        const secondPage = [
            makeTrade({
                id: 21,
                symbol: "TRADE-21",
            }),
        ];

        fetchMock
            .mockResolvedValueOnce(accountsResponse())
            .mockResolvedValueOnce(tradesResponse(firstPage, true, 21))
            .mockResolvedValueOnce(tradesResponse(secondPage, true, 21, 2))
            .mockResolvedValueOnce(response(null))
            .mockResolvedValueOnce(tradesResponse(firstPage, true, 20));

        render(<TradesPage />);

        await screen.findByText("TRADE-1");

        fireEvent.click(screen.getByRole("button", { name: "2" }));

        await screen.findByText("TRADE-21");

        fireEvent.click(
            screen.getByRole("button", { name: "Delete trade 21" }),
        );

        expect(await screen.findByText("TRADE-1")).toBeInTheDocument();

        expect(fetchMock).toHaveBeenLastCalledWith(
            "http://127.0.0.1:8000/trades?account_id=7&page=1&page_size=20",
            expect.anything(),
        );
    });

    test("does not reload when delete fails", async () => {
        fetchMock
            .mockResolvedValueOnce(accountsResponse())
            .mockResolvedValueOnce(tradesResponse([makeTrade()]))
            .mockResolvedValueOnce(tradesResponse([], false));

        render(<TradesPage />);

        await screen.findByText("EURUSD");

        fireEvent.click(
            screen.getByRole("button", { name: "Delete trade 1" }),
        );

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledTimes(3);
        });
    });

    test("stops delete when session is missing", async () => {
        mockGetSession
            .mockResolvedValueOnce(sessionResponse())
            .mockResolvedValueOnce(sessionResponse())
            .mockResolvedValueOnce(sessionResponse(null));

        await renderLoadedPage();

        fireEvent.click(
            screen.getByRole("button", { name: "Delete trade 1" }),
        );

        await waitFor(() => {
            expect(mockPush).toHaveBeenCalledWith("/login");
        });

        expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    test("covers successful delete when selected account becomes null", async () => {
        const { rerender } = await renderLoadedPage();

        await movePageToNoAccounts(rerender);

        fetchMock.mockResolvedValueOnce(tradesResponse());

        expect(tableCallbacks.onDelete).not.toBeNull();

        await act(async () => {
            await tableCallbacks.onDelete!(1);
        });

        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/trades/1",
            expect.objectContaining({
                method: "DELETE",
            }),
        );

        expect(fetchMock).toHaveBeenCalledTimes(4);
    });

    test("filters trades with date presets and resets pagination", async () => {
        const firstPage = makeTrades(20);

        const secondPage = [
            makeTrade({
                id: 21,
                symbol: "TRADE-21",
            }),
        ];

        fetchMock
            .mockResolvedValueOnce(accountsResponse())
            .mockResolvedValueOnce(tradesResponse(firstPage, true, 21))
            .mockResolvedValueOnce(tradesResponse(secondPage, true, 21, 2))
            .mockResolvedValueOnce(tradesResponse([]))
            .mockResolvedValueOnce(tradesResponse([]))
            .mockResolvedValueOnce(tradesResponse(firstPage, true, 21));

        render(<TradesPage />);

        await screen.findByText("TRADE-1");

        fireEvent.click(screen.getByRole("button", { name: "2" }));

        await screen.findByText("TRADE-21");

        fireEvent.click(screen.getByRole("button", { name: "Last 30 days" }));

        await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));

        const thirtyDayUrl = new URL(String(fetchMock.mock.calls[3][0]));
        const thirtyDayFrom = new Date(thirtyDayUrl.searchParams.get("date_from")!);
        const thirtyDayTo = new Date(thirtyDayUrl.searchParams.get("date_to")!);

        expect(thirtyDayUrl.searchParams.get("page")).toBe("1");

        expect(
            (thirtyDayTo.getTime() - thirtyDayFrom.getTime()) / 86_400_000,
        ).toBe(29);

        fireEvent.click(screen.getByRole("button", { name: "Last 90 days" }));

        await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(5));

        const ninetyDayUrl = new URL(String(fetchMock.mock.calls[4][0]));
        const ninetyDayFrom = new Date(ninetyDayUrl.searchParams.get("date_from")!);
        const ninetyDayTo = new Date(ninetyDayUrl.searchParams.get("date_to")!);

        expect(
            (ninetyDayTo.getTime() - ninetyDayFrom.getTime()) / 86_400_000,
        ).toBe(89);

        fireEvent.click(screen.getByRole("button", { name: "All time" }));

        await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(6));

        expect(fetchMock.mock.calls[5][0]).toBe(
            "http://127.0.0.1:8000/trades?account_id=7&page=1&page_size=20",
        );
    });

    test("waits for a complete valid custom date range", async () => {
        fetchMock
            .mockResolvedValueOnce(accountsResponse())
            .mockResolvedValueOnce(tradesResponse([makeTrade()]))
            .mockResolvedValueOnce(tradesResponse([]));

        render(<TradesPage />);

        await screen.findByText("EURUSD");

        expect(fetchMock).toHaveBeenCalledTimes(2);

        fireEvent.click(screen.getByRole("button", { name: "Custom" }));

        fireEvent.change(screen.getByLabelText("From"), {
            target: {
                value: "2026-08-01",
            },
        });

        expect(fetchMock).toHaveBeenCalledTimes(2);

        fireEvent.change(screen.getByLabelText("To"), {
            target: {
                value: "2026-08-31",
            },
        });

        await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));

        expect(fetchMock).toHaveBeenLastCalledWith(
            "http://127.0.0.1:8000/trades?account_id=7&page=1&page_size=20&date_from=2026-08-01&date_to=2026-08-31",
            expect.anything(),
        );

        fireEvent.change(screen.getByLabelText("From"), {
            target: {
                value: "2026-09-05",
            },
        });

        expect(screen.getByRole("alert")).toHaveTextContent(
            "Start date cannot be after end date.",
        );

        expect(fetchMock).toHaveBeenCalledTimes(3);
    });

    test("logs out", async () => {
        await renderLoadedPage();

        fireEvent.click(
            screen.getByRole("button", { name: "Fake logout" }),
        );

        await waitFor(() => {
            expect(mockSignOut).toHaveBeenCalledOnce();
            expect(mockPush).toHaveBeenCalledWith("/login");
        });
    });
});