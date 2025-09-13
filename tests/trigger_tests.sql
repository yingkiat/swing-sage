-- Test file for trigger functionality with 3 events
-- Tests the spine-to-ribs trigger system with funding, analysis, and trade events

-- Test file starts with clean database state

-- ============================================================================
-- TEST 1: FUNDING EVENT → v_funding table
-- ============================================================================
-- Simulates: User reports account funding
-- Expected: Creates record in v_funding with running balance

INSERT INTO events (
    event_id, ts_event, ts_recorded, event_type, category, session_id, 
    event_key, sequence_num, topic, symbols, confidence_score, payload
) VALUES (
    'aaaaaaaa-1111-1111-1111-111111111111',
    '2025-09-08T15:30:00+08:00',
    '2025-09-08T15:30:00+08:00',
    'observation',
    'general',
    'test-funding-session-12345',
    'observation|general|GENERAL_TRADING|currency=usd;funding_amount=414.39;price_level=414.39;transaction_type=account_funding|v1',
    1,
    'general_trading',
    '{}',
    0.85,
    '{"parameters": {"currency": "USD", "price_level": 414.39, "funding_amount": 414.39, "transaction_type": "account_funding"}, "user_command": "I funded USD $414.39 into my trading account", "agent_reasoning": "User reported funding their trading account with $414.39 USD", "extracted_symbols": [], "confidence_indicators": {"source": "user_reported", "data_quality": "high"}, "classification_confidence": 0.85, "structured_analysis": {}}'::jsonb
);

-- Verify funding trigger results
SELECT 'TEST 1 - FUNDING EVENT' as test_name;
SELECT 
    transaction_type, 
    amount, 
    running_balance, 
    description,
    source_event_id = 'aaaaaaaa-1111-1111-1111-111111111111' as correct_source
FROM v_funding 
WHERE source_event_id = 'aaaaaaaa-1111-1111-1111-111111111111';

-- Expected result:
-- transaction_type: DEPOSIT
-- amount: 414.39
-- running_balance: 414.39
-- description: Account funding

-- ============================================================================
-- TEST 2: ANALYSIS EVENT → v_analyses table
-- ============================================================================
-- Simulates: Agent provides GME earnings analysis
-- Expected: Creates record in v_analyses with confidence, recommendations, etc.

INSERT INTO events (
    event_id, ts_event, ts_recorded, event_type, category, session_id,
    event_key, sequence_num, topic, symbols, confidence_score, payload
) VALUES (
    'bbbbbbbb-2222-2222-2222-222222222222',
    '2025-09-08T20:15:00+08:00',
    '2025-09-08T20:15:00+08:00',
    'analysis',
    'earnings',
    'test-analysis-session-67890',
    'analysis|earnings|GME|change_percent=1.94;confidence=6/10;current_price=23.1;earnings_date=9/9/2025;entry_range=1.00-1.25;expected_earnings_move=25-35%;expiration=9/20/2025;recommended_contracts=3;recommended_strike=25;total_risk=375|v1',
    1,
    'GME',
    '{GME}',
    0.95,
    '{"parameters": {"confidence": "6/10", "expiration": "9/20/2025", "total_risk": 375, "entry_range": "1.00-1.25", "current_price": 23.1, "earnings_date": "9/9/2025", "change_percent": 1.94, "recommended_strike": 25, "recommended_contracts": 3, "expected_earnings_move": "25-35%"}, "user_command": "push this to memory", "agent_reasoning": "Comprehensive GME earnings options analysis for 9/9/2025 earnings. User seeks $500 call options play believing GME is overdue for blowout with limited downside. Full workflow analysis: Portfolio strategist flagged high-risk binary event requiring <2% allocation. Price analyst bullish on setup at $23.10, recommends $25 calls with 8/10 confidence expecting 25-35% earnings moves. Risk manager warns 80-85% total loss probability, recommends position reduction. Trade orchestrator final verdict: 3x GME $25 calls (9/20 exp) for $375 total risk, entry $1.00-1.25 per contract before 2 PM, exit within 48 hours post-earnings. Technical setup shows pre-earnings accumulation at $23.10 (+1.94%), volume 1.56M elevated, bullish positioning near day highs.", "extracted_symbols": ["GME"], "confidence_indicators": {"data_quality": "high", "ibkr_live_data": true, "full_workflow_analysis": true, "risk_assessment_completed": true}, "classification_confidence": 0.95, "structured_analysis": {"recommendation": "3x GME $25 calls (9/20 exp)", "action": "BUY_CALLS", "confidence": 0.6, "price_levels": {"entry_price": 1.125, "stop_loss": 0.50, "target_price": 2.50}, "trade_parameters": {"contracts": 3, "strike_price": 25.0, "expiration": "2025-09-20", "option_type": "calls"}}}'::jsonb
);

-- Verify analysis trigger results
SELECT 'TEST 2 - ANALYSIS EVENT' as test_name;
SELECT 
    symbol,
    analysis_type,
    confidence_score,
    created_time,
    source_event_id = 'bbbbbbbb-2222-2222-2222-222222222222' as correct_source
FROM v_analyses 
WHERE source_event_id = 'bbbbbbbb-2222-2222-2222-222222222222';

-- Expected result:
-- symbol: GME
-- analysis_type: earnings_analysis
-- confidence_score: 0.6 (6/10)
-- created_time: 2025-09-08T20:15:00+08:00

-- ============================================================================
-- TEST 3: TRADE EVENT → v_trades, v_positions, v_funding tables
-- ============================================================================
-- Simulates: User executes GME options purchase
-- Expected: Creates records in v_trades (with options details), v_positions (options position), v_funding (cash deduction)

INSERT INTO events (
    event_id, ts_event, ts_recorded, event_type, category, session_id,
    event_key, sequence_num, topic, symbols, confidence_score, payload
) VALUES (
    'cccccccc-3333-3333-3333-333333333333',
    '2025-09-09T10:45:00+08:00',
    '2025-09-09T10:45:00+08:00',
    'observation',
    'earnings',
    'test-trade-session-13579',
    'observation|earnings|GME|contracts=4;entry_price=0.97;expiration=2025-09-26;option_type=calls;symbol=gme;total_cost=388|v1',
    1,
    'GME',
    '{GME}',
    0.95,
    '{"parameters": {"symbol": "GME", "contracts": 4, "expiration": "2025-09-26", "total_cost": 388, "entry_price": 0.97, "option_type": "calls", "strike_price": 25.0}, "user_command": "I bought 4 calls of GME for 26 Sep 2025. Price of purchase was 97 cents.", "agent_reasoning": "User executed GME call options purchase: 4 contracts, Sep 26 2025 expiration, entry price $0.97 per contract. Total cost $388. This follows yesterdays earnings analysis that recommended 3x $25 calls (9/20 exp) at $1.00-1.25 entry. User modified position size (+1 contract) and chose later expiration (Sep 26 vs Sep 20), entered at favorable price within recommended range.", "extracted_symbols": ["GME"], "confidence_indicators": {"data_quality": "high", "execution_within_plan": "mostly_aligned"}, "classification_confidence": 0.95, "structured_analysis": {"action": "BUY", "trade_parameters": {"contracts": 4, "strike_price": 25.0, "expiration": "2025-09-26", "option_type": "calls"}, "price_levels": {"entry_price": 0.97}}}'::jsonb
);

-- Verify trade trigger results - v_trades
SELECT 'TEST 3A - TRADE EVENT → v_trades' as test_name;
SELECT 
    symbol,
    side,
    quantity,
    price,
    total_value,
    instrument_type,
    expiration_date,
    option_type,
    strategy,
    source_event_id = 'cccccccc-3333-3333-3333-333333333333' as correct_source
FROM v_trades 
WHERE source_event_id = 'cccccccc-3333-3333-3333-333333333333';

-- Expected result:
-- symbol: GME, side: BUY, quantity: 4, price: 0.97, total_value: 388
-- instrument_type: option, expiration_date: 2025-09-26, option_type: calls

-- Verify trade trigger results - v_positions
SELECT 'TEST 3B - TRADE EVENT → v_positions' as test_name;
SELECT 
    symbol,
    quantity,
    avg_cost,
    instrument_type,
    expiration_date,
    option_type,
    'cccccccc-3333-3333-3333-333333333333' = ANY(source_events) as correct_source
FROM v_positions 
WHERE symbol = 'GME' AND instrument_type = 'option';

-- Expected result:
-- symbol: GME, quantity: 4, avg_cost: 0.97
-- instrument_type: option, expiration_date: 2025-09-26, option_type: calls

-- Verify trade trigger results - v_funding (cash deduction)
SELECT 'TEST 3C - TRADE EVENT → v_funding (cash deduction)' as test_name;
SELECT 
    transaction_type,
    amount,
    running_balance,
    description,
    source_event_id = 'cccccccc-3333-3333-3333-333333333333' as correct_source
FROM v_funding 
WHERE source_event_id = 'cccccccc-3333-3333-3333-333333333333';

-- Expected result:
-- transaction_type: WITHDRAWAL, amount: -388, running_balance: 26.39 (414.39 - 388)
-- description: Options purchase: 4x GME calls

-- ============================================================================
-- SUMMARY TEST RESULTS
-- ============================================================================
SELECT 'SUMMARY - Total records created' as test_name;
SELECT 
    (SELECT COUNT(*) FROM v_funding) as funding_records,
    (SELECT COUNT(*) FROM v_analyses) as analysis_records, 
    (SELECT COUNT(*) FROM v_trades) as trade_records,
    (SELECT COUNT(*) FROM v_positions) as position_records,
    (SELECT running_balance FROM v_funding ORDER BY transaction_time DESC LIMIT 1) as final_cash_balance;

-- Expected final state:
-- funding_records: 2 (initial deposit + trade withdrawal)
-- analysis_records: 1 (GME analysis)
-- trade_records: 1 (GME options purchase)
-- position_records: 1 (GME options position)
-- final_cash_balance: 26.39

-- ============================================================================
-- AUTOMATIC CLEANUP - Remove test records after verification
-- ============================================================================

-- Remove v_* table records created by the test triggers
DELETE FROM v_portfolio_snapshots WHERE trigger_event_id IN (
    'aaaaaaaa-1111-1111-1111-111111111111',
    'bbbbbbbb-2222-2222-2222-222222222222', 
    'cccccccc-3333-3333-3333-333333333333'
);

DELETE FROM v_analyses WHERE source_event_id IN (
    'aaaaaaaa-1111-1111-1111-111111111111',
    'bbbbbbbb-2222-2222-2222-222222222222',
    'cccccccc-3333-3333-3333-333333333333'
);

DELETE FROM v_trades WHERE source_event_id IN (
    'aaaaaaaa-1111-1111-1111-111111111111',
    'bbbbbbbb-2222-2222-2222-222222222222',
    'cccccccc-3333-3333-3333-333333333333'
);

DELETE FROM v_positions WHERE source_events && ARRAY[
    'aaaaaaaa-1111-1111-1111-111111111111'::uuid,
    'bbbbbbbb-2222-2222-2222-222222222222'::uuid,
    'cccccccc-3333-3333-3333-333333333333'::uuid
];

DELETE FROM v_funding WHERE source_event_id IN (
    'aaaaaaaa-1111-1111-1111-111111111111',
    'bbbbbbbb-2222-2222-2222-222222222222',
    'cccccccc-3333-3333-3333-333333333333'
);

-- Remove the original events (spine records)
DELETE FROM events WHERE event_id IN (
    'aaaaaaaa-1111-1111-1111-111111111111',
    'bbbbbbbb-2222-2222-2222-222222222222',
    'cccccccc-3333-3333-3333-333333333333'
);

-- Verify cleanup completed
SELECT 'CLEANUP COMPLETED' as cleanup_status;
SELECT 
    (SELECT COUNT(*) FROM v_funding WHERE source_event_id IN ('aaaaaaaa-1111-1111-1111-111111111111','bbbbbbbb-2222-2222-2222-222222222222','cccccccc-3333-3333-3333-333333333333')) as remaining_funding,
    (SELECT COUNT(*) FROM v_analyses WHERE source_event_id IN ('aaaaaaaa-1111-1111-1111-111111111111','bbbbbbbb-2222-2222-2222-222222222222','cccccccc-3333-3333-3333-333333333333')) as remaining_analyses,
    (SELECT COUNT(*) FROM v_trades WHERE source_event_id IN ('aaaaaaaa-1111-1111-1111-111111111111','bbbbbbbb-2222-2222-2222-222222222222','cccccccc-3333-3333-3333-333333333333')) as remaining_trades,
    (SELECT COUNT(*) FROM v_positions WHERE source_events && ARRAY['aaaaaaaa-1111-1111-1111-111111111111'::uuid,'bbbbbbbb-2222-2222-2222-222222222222'::uuid,'cccccccc-3333-3333-3333-333333333333'::uuid]) as remaining_positions,
    (SELECT COUNT(*) FROM events WHERE event_id IN ('aaaaaaaa-1111-1111-1111-111111111111','bbbbbbbb-2222-2222-2222-222222222222','cccccccc-3333-3333-3333-333333333333')) as remaining_events;

-- Final commit to ensure cleanup persists
COMMIT;