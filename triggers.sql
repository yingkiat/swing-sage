-- Database triggers to auto-update v_ tables from spine events
-- This removes the burden from Claude to manually update portfolio ribs

-- Function to parse JSON parameters and detect portfolio actions
CREATE OR REPLACE FUNCTION process_portfolio_event()
RETURNS TRIGGER AS $$
DECLARE
    params JSONB;
    structured_data JSONB;
    trade_params JSONB;
    symbol_val TEXT;
    quantity_val INTEGER;
    price_val DECIMAL(10,2);
    total_cost_val DECIMAL(12,2);
    option_type_val TEXT;
    expiration_val DATE;
    transaction_type_val TEXT;
    funding_amount_val NUMERIC;
    current_balance NUMERIC;
BEGIN
    -- Parse parameters JSON from payload
    params := (NEW.payload->>'parameters')::JSONB;
    
    -- TRADE DETECTION: Look for structured trade parameters
    structured_data := NEW.payload->'structured_analysis';
    trade_params := structured_data->'trade_parameters';
    
    -- Check for options trade in structured data
    IF trade_params ? 'contracts' AND trade_params ? 'strike_price' THEN
        -- Options trade detected from structured analysis
        symbol_val := COALESCE((NEW.symbols)[1], params->>'symbol');
        quantity_val := (trade_params->>'contracts')::INTEGER;
        price_val := COALESCE((structured_data->'price_levels'->>'entry_price')::DECIMAL(10,2), (trade_params->>'strike_price')::DECIMAL(10,2));
        total_cost_val := quantity_val * price_val * 100; -- Options multiplier
        option_type_val := trade_params->>'option_type';
        
        -- Insert into v_trades using structured data
        INSERT INTO v_trades (
            symbol, side, quantity, price, total_value, commission,
            execution_time, strategy, instrument_type, strike_price, expiration_date, option_type, source_event_id
        ) VALUES (
            symbol_val, 
            CASE 
                WHEN structured_data->>'action' = 'BUY_CALLS' THEN 'BUY'
                WHEN structured_data->>'action' = 'BUY_PUTS' THEN 'BUY'
                WHEN structured_data->>'action' = 'SELL_CALLS' THEN 'SELL'
                WHEN structured_data->>'action' = 'SELL_PUTS' THEN 'SELL'
                ELSE COALESCE(structured_data->>'action', 'BUY')
            END, -- Use structured action but truncate to fit VARCHAR(4)
            quantity_val, 
            price_val, 
            total_cost_val, 
            0.0, -- Default commission
            NEW.ts_event, 
            COALESCE(NEW.category, 'options_trade'), -- Use event category as strategy
            'option', 
            (trade_params->>'strike_price')::DECIMAL(10,2),
            (trade_params->>'expiration')::DATE, 
            option_type_val, 
            NEW.event_id
        );
        
        -- Update v_positions (upsert)
        INSERT INTO v_positions (
            symbol, quantity, avg_cost, first_entry, last_activity, current_value, unrealized_pnl,
            instrument_type, strike_price, expiration_date, option_type, source_events
        ) VALUES (
            symbol_val, quantity_val, price_val, NEW.ts_event, NEW.ts_event,
            total_cost_val, -- Initial current_value = cost basis
            0.0, -- Initial unrealized_pnl = 0
            'option', 
            (trade_params->>'strike_price')::DECIMAL(10,2),
            (trade_params->>'expiration')::DATE, 
            option_type_val, 
            ARRAY[NEW.event_id]
        )
        ON CONFLICT (symbol, instrument_type, strike_price, expiration_date, option_type) DO UPDATE SET
            quantity = v_positions.quantity + quantity_val,
            avg_cost = ((v_positions.quantity * v_positions.avg_cost) + total_cost_val) / (v_positions.quantity + quantity_val),
            current_value = v_positions.current_value + total_cost_val, -- Add to current value
            last_activity = NEW.ts_event,
            source_events = array_append(v_positions.source_events, NEW.event_id);
        
        -- Update cash position (deduct purchase cost)
        SELECT running_balance::NUMERIC INTO current_balance 
        FROM v_funding 
        ORDER BY transaction_time DESC 
        LIMIT 1;
        
        IF current_balance IS NULL THEN current_balance := 0; END IF;
        
        INSERT INTO v_funding (
            transaction_type, amount, transaction_time, 
            description, running_balance, source_event_id
        ) VALUES (
            'WITHDRAWAL', -total_cost_val, NEW.ts_event,
            'Options purchase: ' || quantity_val || 'x ' || symbol_val || ' ' || option_type_val,
            COALESCE(current_balance, 0::DECIMAL(15,2)) - total_cost_val, NEW.event_id
        );
        
    END IF;
    
    -- FUNDING DETECTION: Look for account funding
    IF params ? 'funding_amount' AND params ? 'transaction_type' THEN
        funding_amount_val := (params->>'funding_amount')::NUMERIC;
        transaction_type_val := UPPER(params->>'transaction_type');
        
        -- Get current balance
        SELECT running_balance::NUMERIC INTO current_balance 
        FROM v_funding 
        ORDER BY transaction_time DESC 
        LIMIT 1;
        
        IF current_balance IS NULL THEN current_balance := 0; END IF;
        
        -- Only insert if not already exists (avoid duplicates)
        IF NOT EXISTS (SELECT 1 FROM v_funding WHERE source_event_id = NEW.event_id) THEN
            INSERT INTO v_funding (
                transaction_type, amount, transaction_time,
                description, running_balance, source_event_id
            ) VALUES (
                CASE WHEN transaction_type_val = 'ACCOUNT_FUNDING' THEN 'DEPOSIT' ELSE transaction_type_val END,
                funding_amount_val, NEW.ts_event,
                'Account funding', COALESCE(current_balance, 0::NUMERIC) + funding_amount_val, NEW.event_id
            );
        END IF;
    END IF;
    
    -- ANALYSIS DETECTION: Store analysis results using structured data
    IF NEW.event_type = 'analysis' THEN
        DECLARE
            structured_data JSONB;
            price_levels JSONB;
            extracted_recommendation TEXT;
            extracted_confidence DECIMAL(3,2);
            extracted_target_price DECIMAL(10,2);
        BEGIN
            structured_data := NEW.payload->'structured_analysis';
            price_levels := structured_data->'price_levels';
            
            -- Use structured recommendation (much simpler!)
            extracted_recommendation := COALESCE(
                structured_data->>'recommendation',
                structured_data->>'action',
                'ANALYZE'
            );
            
            -- Use structured confidence score
            extracted_confidence := COALESCE(
                (structured_data->>'confidence')::DECIMAL(3,2),
                (params->>'confidence')::DECIMAL(3,2) / 10.0,
                NEW.confidence_score
            );
            
            -- Use structured price levels
            extracted_target_price := COALESCE(
                (price_levels->>'target_price')::DECIMAL(10,2),
                (price_levels->>'entry_price')::DECIMAL(10,2),
                (params->>'current_price')::DECIMAL(10,2)
            );
            
            INSERT INTO v_analyses (
                symbol, analysis_type, recommendation, confidence_score,
                target_price, stop_loss, timeframe, outcome, created_time, source_event_id
            ) VALUES (
                COALESCE((NEW.symbols)[1], params->>'symbol'),
                NEW.category || '_analysis',
                extracted_recommendation,
                extracted_confidence,
                extracted_target_price,
                (price_levels->>'stop_loss')::DECIMAL(10,2),
                params->>'timeframe',
                'PENDING', -- Outcome determined later when position is closed
                NEW.ts_event,
                NEW.event_id
            );
        END;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on events table
DROP TRIGGER IF EXISTS portfolio_update_trigger ON events;
CREATE TRIGGER portfolio_update_trigger
    AFTER INSERT ON events
    FOR EACH ROW
    EXECUTE FUNCTION process_portfolio_event();

-- Trigger to create portfolio snapshots on significant events
CREATE OR REPLACE FUNCTION create_portfolio_snapshot()
RETURNS TRIGGER AS $$
DECLARE
    total_val DECIMAL(15,2);
    cash_bal DECIMAL(15,2);
    invested_val DECIMAL(15,2);
    position_count INTEGER;
BEGIN
    -- Calculate portfolio metrics
    SELECT COALESCE(SUM(current_value), 0) INTO invested_val FROM v_positions WHERE quantity != 0;
    SELECT COALESCE(running_balance, 0) INTO cash_bal FROM v_funding ORDER BY transaction_time DESC LIMIT 1;
    SELECT COUNT(*) INTO position_count FROM v_positions WHERE quantity != 0;
    
    total_val := cash_bal + invested_val;
    
    -- Create snapshot on funding or major trades
    IF NEW.transaction_type = 'DEPOSIT' OR (NEW.amount IS NOT NULL AND ABS(NEW.amount) > 100) THEN
        INSERT INTO v_portfolio_snapshots (
            snapshot_time, total_value, cash_balance, invested_value,
            unrealized_pnl, realized_pnl, num_positions, trigger_event_id
        ) VALUES (
            NEW.transaction_time, total_val, cash_bal, invested_val,
            0, 0, position_count, NEW.source_event_id
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create snapshot trigger
DROP TRIGGER IF EXISTS portfolio_snapshot_trigger ON v_funding;
CREATE TRIGGER portfolio_snapshot_trigger
    AFTER INSERT ON v_funding
    FOR EACH ROW
    EXECUTE FUNCTION create_portfolio_snapshot();