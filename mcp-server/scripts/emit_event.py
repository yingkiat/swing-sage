#!/usr/bin/env python3
"""
MVP3 Event Emission Script - Unified Memory Storage
Handles user-triggered event storage with AI context extraction.
"""

import os
import sys
import json
import argparse
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional
import psycopg2
from rich.console import Console
from dotenv import load_dotenv
import re

console = Console()

def parse_database_url(database_url: str) -> dict:
    """Parse PostgreSQL URL into components."""
    if database_url.startswith('postgresql://'):
        url_part = database_url[13:]
        
        if '@' in url_part:
            auth_part, host_db_part = url_part.split('@', 1)
            if ':' in auth_part:
                user, password = auth_part.split(':', 1)
            else:
                user, password = auth_part, ''
        else:
            user, password = 'postgres', ''
            host_db_part = url_part
        
        if '/' in host_db_part:
            host_port, database = host_db_part.rsplit('/', 1)
        else:
            host_port, database = host_db_part, 'postgres'
        
        if ':' in host_port:
            host, port = host_port.rsplit(':', 1)
            port = int(port)
        else:
            host, port = host_port, 5432
        
        return {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database
        }
    else:
        raise ValueError(f"Unsupported database URL format: {database_url}")

def extract_topic_from_context(conversation_context: Dict[str, Any], user_command: str) -> Tuple[str, List[str]]:
    """Extract the main topic and related symbols from conversation context."""
    recent_symbols = conversation_context.get('recent_symbols', [])
    agent_reasoning = conversation_context.get('agent_reasoning', '')
    
    # Primary topic determination
    if recent_symbols and len(recent_symbols) == 1:
        # Single symbol - use it as the topic
        topic = recent_symbols[0].upper()
        symbols = [topic]
    elif recent_symbols and len(recent_symbols) > 1:
        # Multiple symbols - create topic from them
        symbols = [s.upper() for s in recent_symbols]
        topic = '_'.join(sorted(symbols))
    else:
        # No symbols provided, infer from context
        if 'market' in agent_reasoning.lower():
            topic = 'market_analysis'
            symbols = []
        elif 'earnings' in agent_reasoning.lower():
            topic = 'earnings_analysis'
            symbols = []
        elif 'volatility' in agent_reasoning.lower():
            topic = 'market_volatility'
            symbols = []
        else:
            topic = 'general_trading'
            symbols = []
    
    return topic, symbols

def extract_parameters(agent_reasoning: str, conversation_context: str) -> Dict[str, Any]:
    """Extract and normalize parameters from context."""
    params = {}
    
    # Extract price levels
    price_matches = re.findall(r'\$(\d+(?:\.\d+)?)', conversation_context)
    if price_matches:
        params['price_level'] = float(price_matches[0])
    
    # Extract RSI values
    rsi_matches = re.findall(r'RSI\s+(?:at\s+|of\s+|=\s*)?(\d+(?:\.\d+)?)', conversation_context, re.IGNORECASE)
    if rsi_matches:
        params['rsi'] = float(rsi_matches[0])
    
    # Extract volume ratios
    volume_matches = re.findall(r'(\d+(?:\.\d+)?)x\s+(?:average|avg)', conversation_context, re.IGNORECASE)
    if volume_matches:
        params['volume_ratio'] = f"{volume_matches[0]}x"
    
    # Extract timeframes
    timeframe_patterns = [
        r'(\d+)[-\s]?(?:day|d)\b',  # 3-day, 3 day, 3d
        r'(\d+)[-\s]?(?:hour|h)\b',  # 2-hour, 2h
        r'(\d+)[-\s]?(?:minute|min|m)\b',  # 15-minute, 15m
        r'\b(daily|weekly|monthly)\b',
    ]
    
    for pattern in timeframe_patterns:
        matches = re.findall(pattern, conversation_context, re.IGNORECASE)
        if matches:
            params['timeframe'] = matches[0].lower()
            break
    
    # Extract support/resistance levels
    support_matches = re.findall(r'support\s+(?:at\s+|around\s+)?\$?(\d+(?:\.\d+)?)', conversation_context, re.IGNORECASE)
    if support_matches:
        params['support_level'] = float(support_matches[0])
    
    resistance_matches = re.findall(r'resistance\s+(?:at\s+|around\s+)?\$?(\d+(?:\.\d+)?)', conversation_context, re.IGNORECASE)
    if resistance_matches:
        params['resistance_level'] = float(resistance_matches[0])
    
    return params

def extract_reasoning_chain(agent_reasoning: str) -> Dict[str, Any]:
    """Extract structured reasoning chain from agent analysis."""
    reasoning_chain = {
        'steps': [],
        'overall_confidence': None,
        'decision_framework': None
    }

    # Look for reasoning chain analysis sections
    chain_patterns = [
        r'## REASONING CHAIN ANALYSIS(.*?)(?=##|$)',
        r'## RISK ASSESSMENT CHAIN(.*?)(?=##|$)'
    ]

    for pattern in chain_patterns:
        match = re.search(pattern, agent_reasoning, re.DOTALL | re.IGNORECASE)
        if match:
            chain_content = match.group(1)

            # Extract individual steps
            step_pattern = r'### Step (\d+):\s*([^\n]+)(.*?)(?=### Step|\Z)'
            step_matches = re.finditer(step_pattern, chain_content, re.DOTALL | re.IGNORECASE)

            for step_match in step_matches:
                step_num = int(step_match.group(1))
                step_title = step_match.group(2).strip()
                step_content = step_match.group(3)

                # Extract step details
                step_data = {
                    'step_id': step_num,
                    'title': step_title,
                    'reasoning': '',
                    'evidence': '',
                    'confidence': None,
                    'alternatives': '',
                    'dependencies': ''
                }

                # Parse step content for structured data
                reasoning_match = re.search(r'\*\*Reasoning\*\*:\s*([^\n]+)', step_content, re.IGNORECASE)
                if reasoning_match:
                    step_data['reasoning'] = reasoning_match.group(1).strip()

                evidence_match = re.search(r'\*\*Evidence\*\*:\s*([^\n]+)', step_content, re.IGNORECASE)
                if evidence_match:
                    step_data['evidence'] = evidence_match.group(1).strip()

                confidence_match = re.search(r'\*\*Confidence\*\*:\s*(\d+)/10', step_content, re.IGNORECASE)
                if confidence_match:
                    step_data['confidence'] = float(confidence_match.group(1)) / 10

                alternatives_match = re.search(r'\*\*Alternatives Considered\*\*:\s*([^\n]+)', step_content, re.IGNORECASE)
                if alternatives_match:
                    step_data['alternatives'] = alternatives_match.group(1).strip()

                dependencies_match = re.search(r'\*\*Dependencies\*\*:\s*([^\n]+)', step_content, re.IGNORECASE)
                if dependencies_match:
                    step_data['dependencies'] = dependencies_match.group(1).strip()

                reasoning_chain['steps'].append(step_data)

    # Extract overall confidence from final synthesis
    overall_confidence_match = re.search(r'\*\*Overall.*?Confidence\*\*:\s*(\d+)/10', agent_reasoning, re.IGNORECASE)
    if overall_confidence_match:
        reasoning_chain['overall_confidence'] = float(overall_confidence_match.group(1)) / 10

    return reasoning_chain if reasoning_chain['steps'] else None

def extract_decision_synthesis(agent_reasoning: str) -> Dict[str, Any]:
    """Extract decision synthesis chain from trade-orchestrator output."""
    synthesis = {}

    # Look for decision synthesis section
    synthesis_pattern = r'## DECISION SYNTHESIS CHAIN(.*?)(?=##|$)'
    match = re.search(synthesis_pattern, agent_reasoning, re.DOTALL | re.IGNORECASE)

    if match:
        synthesis_content = match.group(1)

        # Extract consolidation process
        consolidation_data = {}
        proposer_weight = re.search(r'\*\*Proposer Input Weight\*\*:\s*(\d+)%\s*-\s*([^\n]+)', synthesis_content, re.IGNORECASE)
        if proposer_weight:
            consolidation_data['proposer_weight'] = int(proposer_weight.group(1))
            consolidation_data['proposer_rationale'] = proposer_weight.group(2).strip()

        counterer_weight = re.search(r'\*\*Counterer Input Weight\*\*:\s*(\d+)%\s*-\s*([^\n]+)', synthesis_content, re.IGNORECASE)
        if counterer_weight:
            consolidation_data['counterer_weight'] = int(counterer_weight.group(1))
            consolidation_data['counterer_rationale'] = counterer_weight.group(2).strip()

        if consolidation_data:
            synthesis['consolidation_process'] = consolidation_data

        # Extract decision tree scenarios
        decision_tree = {}
        primary_scenario = re.search(r'\*\*Primary Path\*\*\s*\((\d+)%\s*probability\):\s*([^\n]+)', synthesis_content, re.IGNORECASE)
        if primary_scenario:
            decision_tree['primary_scenario'] = {
                'probability': float(primary_scenario.group(1)) / 100,
                'outcome': primary_scenario.group(2).strip()
            }

        # Extract alternative scenarios
        alt_scenarios = []
        scenario_pattern = r'-\s*Scenario [A-Z]\s*\((\d+)%\s*probability\):\s*([^\n]+)'
        for scenario_match in re.finditer(scenario_pattern, synthesis_content, re.IGNORECASE):
            alt_scenarios.append({
                'probability': float(scenario_match.group(1)) / 100,
                'outcome': scenario_match.group(2).strip()
            })

        if alt_scenarios:
            decision_tree['alternative_scenarios'] = alt_scenarios

        if decision_tree:
            synthesis['decision_tree'] = decision_tree

        # Extract synthesis logic
        synthesis_logic = re.search(r'\*\*Synthesis Logic\*\*:\s*([^\n]+)', synthesis_content, re.IGNORECASE)
        if synthesis_logic:
            synthesis['synthesis_logic'] = synthesis_logic.group(1).strip()

    return synthesis if synthesis else None

def extract_structured_analysis(agent_reasoning: str, context: str) -> Dict[str, Any]:
    """Extract structured data from agent reasoning for database triggers."""
    structured = {}
    combined_text = f"{agent_reasoning} {context}".lower()

    # NEW: Extract reasoning chain analysis for enhanced memory depth
    reasoning_chain = extract_reasoning_chain(agent_reasoning)
    if reasoning_chain:
        structured['reasoning_chain'] = reasoning_chain

    # NEW: Extract decision synthesis (from trade-orchestrator)
    decision_synthesis = extract_decision_synthesis(agent_reasoning)
    if decision_synthesis:
        structured['decision_synthesis'] = decision_synthesis

    # Extract recommendations/actions
    if 'trade orchestrator' in combined_text or 'final verdict' in combined_text:
        # Trade orchestrator output - extract final recommendation
        recommendation_patterns = [
            r'trade orchestrator final verdict:([^.]+)',
            r'final verdict:([^.]+)', 
            r'action:\s*(buy|sell|hold|avoid)',
            r'recommendation:\s*([^.]+)'
        ]
        for pattern in recommendation_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                structured['recommendation'] = match.group(1).strip()
                break
        
        # Extract action
        action_patterns = [
            r'\*\*action\*\*:\s*(buy|sell|hold|avoid)',
            r'action:\s*(buy|sell|hold|avoid)'
        ]
        for pattern in action_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                structured['action'] = match.group(1).upper()
                break
    
    # Extract price levels
    price_levels = {}
    price_patterns = {
        'entry_price': r'entry[^$]*\$(\d+(?:\.\d{2})?)',
        'stop_loss': r'stop[^$]*\$(\d+(?:\.\d{2})?)',
        'target_price': r'target[^$]*\$(\d+(?:\.\d{2})?)',
        'support_level': r'support[^$]*\$(\d+(?:\.\d{2})?)',
        'resistance_level': r'resistance[^$]*\$(\d+(?:\.\d{2})?)'
    }
    
    for key, pattern in price_patterns.items():
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            price_levels[key] = float(match.group(1))
    
    if price_levels:
        structured['price_levels'] = price_levels
    
    # Extract confidence score
    confidence_patterns = [
        r'confidence:\s*(\d+)/10',
        r'confidence:\s*(\d+(?:\.\d+)?)',
        r'setup quality.*?(\d+)/10'
    ]
    for pattern in confidence_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            score = float(match.group(1))
            structured['confidence'] = score / 10.0 if score > 1 else score
            break
    
    # Extract trade parameters for portfolio actions
    trade_params = {}
    
    # Options trades
    options_patterns = {
        'contracts': r'(\d+)\s*(?:x\s*)?contracts?',
        'strike_price': r'strike[^$]*\$(\d+(?:\.\d{2})?)',
        'expiration': r'expiration[^:]*(\d{1,2}/\d{1,2}/\d{4})',
        'option_type': r'(calls?|puts?)'
    }
    
    for key, pattern in options_patterns.items():
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            if key == 'contracts':
                trade_params[key] = int(match.group(1))
            elif key == 'strike_price':
                trade_params[key] = float(match.group(1))
            elif key == 'option_type':
                trade_params[key] = 'calls' if 'call' in match.group(1).lower() else 'puts'
            else:
                trade_params[key] = match.group(1)
    
    # Stock trades
    stock_patterns = {
        'shares': r'(\d+)\s*shares?',
        'position_size': r'position size[^$]*\$(\d+(?:,\d{3})*(?:\.\d{2})?)'
    }
    
    for key, pattern in stock_patterns.items():
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            if key == 'shares':
                trade_params[key] = int(match.group(1))
            elif key == 'position_size':
                trade_params[key] = float(match.group(1).replace(',', ''))
    
    if trade_params:
        structured['trade_parameters'] = trade_params
    
    return structured

def classify_event(user_command: str, conversation_context: str) -> Tuple[str, str]:
    """Classify event type and category from user command and context."""
    user_cmd_lower = user_command.lower()
    context_lower = conversation_context.lower()
    
    # Event Type Classification
    if any(word in user_cmd_lower for word in ['recommendation', 'buy', 'sell', 'trade']):
        event_type = 'proposal'
    elif any(word in context_lower for word in ['buy', 'sell', 'enter', 'exit', 'target', 'stop']):
        event_type = 'proposal'
    elif any(word in user_cmd_lower for word in ['risk', 'insight']):
        event_type = 'insight'
    elif any(word in user_cmd_lower for word in ['analysis', 'analyze']):
        event_type = 'analysis'
    elif any(word in context_lower for word in ['shows', 'indicates', 'suggests', 'looking', 'setup']):
        event_type = 'analysis'
    else:
        event_type = 'observation'
    
    # Category Classification
    if any(word in context_lower for word in ['swing', 'swing trade', 'swing trading']):
        category = 'swing_setup'
    elif any(word in context_lower for word in ['day trade', 'day trading', 'intraday']):
        category = 'day_trade'
    elif any(word in context_lower for word in ['earnings', 'earnings call', 'quarterly']):
        category = 'earnings'
    elif any(word in context_lower for word in ['risk', 'stop loss', 'position size']):
        category = 'risk_mgmt'
    elif any(word in context_lower for word in ['breakout', 'support', 'resistance', 'technical']):
        category = 'technical_analysis'
    elif any(word in context_lower for word in ['sentiment', 'news', 'catalyst']):
        category = 'sentiment'
    else:
        category = 'general'
    
    return event_type, category

def normalize_param_value(value: Any) -> str:
    """Normalize parameter values for consistent key generation."""
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        else:
            return f"{value:.2f}".rstrip('0').rstrip('.')
    elif isinstance(value, str):
        return value.lower().replace(' ', '_')
    else:
        return str(value)

def generate_event_key(event_type: str, category: str, topic: str, 
                      params: Dict[str, Any], data_version: str = 'v1') -> str:
    """Generate a stable correlation key for the event."""
    # Normalize topic
    topic_canon = topic.upper().replace(' ', '_')
    
    # Canonicalize parameters
    param_pairs = []
    for key in sorted(params.keys()):
        value = normalize_param_value(params[key])
        param_pairs.append(f"{key}={value}")
    params_canon = ';'.join(param_pairs)
    
    # Build key
    return f"{event_type}|{category}|{topic_canon}|{params_canon}|{data_version}"

def detect_portfolio_actions(conversation_context: Dict[str, Any], user_command: str) -> Optional[Dict[str, Any]]:
    """Detect if the conversation contains actual portfolio transactions."""
    agent_reasoning = conversation_context.get('agent_reasoning', '').lower()
    user_cmd_lower = user_command.lower()
    combined_context = f"{agent_reasoning} {user_cmd_lower}".lower()
    
    # Look for funding transactions
    funding_patterns = [
        r'(?:loaded|deposited|added|funded)\s+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'(?:withdrew|withdrawal|took out)\s+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s+(?:into|to)\s+(?:my\s+)?account',
        r'account.*\$(\d+(?:,\d{3})*(?:\.\d{2})?)'
    ]
    
    for pattern in funding_patterns:
        match = re.search(pattern, combined_context)
        if match:
            amount = float(match.group(1).replace(',', ''))
            transaction_type = 'WITHDRAWAL' if any(word in combined_context for word in ['withdrew', 'withdrawal', 'took out']) else 'DEPOSIT'
            
            return {
                'type': 'funding',
                'data': {
                    'amount': amount,
                    'transaction_type': transaction_type,
                    'description': f"User reported: {user_command}"
                }
            }
    
    # Look for trade executions  
    trade_patterns = [
        r'(?:bought|purchased)\s+(\d+)\s+([A-Z]{1,5})\s+(?:at|@)\s+\$?(\d+(?:\.\d{2})?)',
        r'(?:sold|short)\s+(\d+)\s+([A-Z]{1,5})\s+(?:at|@)\s+\$?(\d+(?:\.\d{2})?)',
        r'(\d+)\s+shares?\s+(?:of\s+)?([A-Z]{1,5})\s+(?:at|@)\s+\$?(\d+(?:\.\d{2})?)',
        r'([A-Z]{1,5})\s+(\d+)\s+(?:shares?\s+)?(?:at|@)\s+\$?(\d+(?:\.\d{2})?)'
    ]
    
    for pattern in trade_patterns:
        match = re.search(pattern, combined_context)
        if match:
            groups = match.groups()
            
            # Handle different pattern structures
            if len(groups) == 3 and groups[1].isalpha():  # quantity, symbol, price
                quantity, symbol, price = int(groups[0]), groups[1].upper(), float(groups[2])
            elif len(groups) == 3 and groups[0].isalpha():  # symbol, quantity, price  
                symbol, quantity, price = groups[0].upper(), int(groups[1]), float(groups[2])
            else:
                continue
                
            side = 'SELL' if any(word in combined_context for word in ['sold', 'short']) else 'BUY'
            total_value = quantity * price
            
            return {
                'type': 'trade', 
                'data': {
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': price,
                    'side': side,
                    'total_value': total_value,
                    'strategy': 'manual_entry'  # User-reported trade
                }
            }
    
    return None

def update_portfolio_ribs(portfolio_action: Dict[str, Any], event_id: str, db_config: dict) -> bool:
    """Update portfolio ribs tables based on detected portfolio actions."""
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        if portfolio_action['type'] == 'funding':
            data = portfolio_action['data']
            
            # Get current running balance
            cursor.execute("SELECT running_balance FROM v_funding ORDER BY transaction_time DESC LIMIT 1")
            result = cursor.fetchone()
            current_balance = float(result[0]) if result else 0.0

            # Calculate new running balance
            if data['transaction_type'] == 'DEPOSIT':
                new_balance = current_balance + float(data['amount'])
            else:  # WITHDRAWAL
                new_balance = current_balance - float(data['amount'])
            
            # Insert funding record
            cursor.execute("""
                INSERT INTO v_funding (
                    transaction_type, amount, transaction_time, description,
                    running_balance, source_event_id
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                data['transaction_type'],
                float(data['amount']),
                datetime.now(timezone.utc),
                data['description'],
                new_balance,
                event_id
            ))
            
        elif portfolio_action['type'] == 'trade':
            data = portfolio_action['data']
            
            # Insert trade record
            cursor.execute("""
                INSERT INTO v_trades (
                    symbol, side, quantity, price, total_value, execution_time,
                    strategy, source_event_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data['symbol'], data['side'], int(data['quantity']), float(data['price']),
                float(data['total_value']), datetime.now(timezone.utc),
                data['strategy'], event_id
            ))
            
            # Update or create position
            if data['side'] == 'BUY':
                shares_delta = int(data['quantity'])
            else:  # SELL
                shares_delta = -int(data['quantity'])
            
            cursor.execute("""
                INSERT INTO v_positions (symbol, shares, avg_cost, first_entry, last_activity, source_events)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE SET
                    shares = v_positions.shares + EXCLUDED.shares,
                    avg_cost = CASE 
                        WHEN EXCLUDED.shares > 0 THEN  -- BUY: update avg cost
                            ((v_positions.shares * v_positions.avg_cost) + 
                             (EXCLUDED.shares * EXCLUDED.avg_cost)) / 
                            NULLIF((v_positions.shares + EXCLUDED.shares), 0)
                        ELSE v_positions.avg_cost  -- SELL: keep same avg cost
                        END,
                    last_activity = EXCLUDED.last_activity,
                    source_events = array_append(v_positions.source_events, %s)
            """, (
                data['symbol'], shares_delta, float(data['price']),
                datetime.now(timezone.utc), datetime.now(timezone.utc),
                [event_id], event_id
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        console.print(f"Error updating portfolio ribs: {e}", style="red")
        return False

def calculate_confidence_score(conversation_context: str, symbols: List[str], params: Dict[str, Any]) -> float:
    """Calculate confidence score based on data quality and specificity."""
    score = 0.5  # Base score
    
    # Boost for specific symbols
    if symbols:
        score += 0.2
    
    # Boost for specific parameters
    if params:
        score += min(0.2, len(params) * 0.05)
    
    # Boost for specific price levels
    if any(key in params for key in ['price_level', 'support_level', 'resistance_level']):
        score += 0.15
    
    # Boost for technical indicators
    if any(key in params for key in ['rsi', 'volume_ratio', 'timeframe']):
        score += 0.1
    
    # Boost for detailed reasoning
    if len(conversation_context) > 100:
        score += 0.05
    
    return min(1.0, score)

def get_next_sequence_number(db_config: dict, session_id: str) -> int:
    """Get the next sequence number for this session."""
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COALESCE(MAX(sequence_num), 0) + 1 FROM events WHERE session_id = %s",
            (session_id,)
        )
        sequence_num = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return sequence_num
        
    except psycopg2.Error as e:
        console.print(f"Error getting sequence number: {e}", style="red")
        return 1

def emit_event(
    user_command: str,
    conversation_context: Dict[str, Any],
    session_id: str,
    data_version: str = 'v1',
    type_hint: str = None,
    symbol_override: List[str] = None,
    db_config: dict = None
) -> Dict[str, Any]:
    """Emit a unified event to the database."""
    
    try:
        # Extract context information
        recent_symbols = conversation_context.get('recent_symbols', [])
        agent_reasoning = conversation_context.get('agent_reasoning', '')
        parameters_used = conversation_context.get('parameters_used', {})
        confidence_indicators = conversation_context.get('confidence_indicators', {})
        
        # Extract topic and symbols from context
        if symbol_override:
            # If symbol override provided, use first symbol as topic
            topic = symbol_override[0].upper()
            symbols = symbol_override
        else:
            # Extract topic and symbols from conversation context
            topic, symbols = extract_topic_from_context(conversation_context, user_command)
        
        # Extract additional parameters from reasoning
        extracted_params = extract_parameters(agent_reasoning, user_command)
        
        # Extract structured analysis from agent reasoning 
        structured_analysis = extract_structured_analysis(agent_reasoning, user_command)
        
        # Merge provided parameters with extracted ones
        all_params = {**parameters_used, **extracted_params}
        
        # Classify event type and category
        if type_hint:
            # Parse type hint (e.g., "analysis" or "analysis/swing_setup")
            if '/' in type_hint:
                event_type, category = type_hint.split('/', 1)
            else:
                event_type = type_hint
                _, category = classify_event(user_command, agent_reasoning)
        else:
            event_type, category = classify_event(user_command, agent_reasoning)
        
        # Generate event key
        event_key = generate_event_key(event_type, category, topic, all_params, data_version)
        
        # Calculate confidence score
        confidence_score = calculate_confidence_score(
            agent_reasoning, symbols, all_params
        )
        
        # Get sequence number
        sequence_num = get_next_sequence_number(db_config, session_id)
        
        # Create event payload with structured analysis
        payload = {
            'user_command': user_command,
            'agent_reasoning': agent_reasoning,
            'parameters': all_params,
            'confidence_indicators': confidence_indicators,
            'extracted_symbols': symbols,
            'classification_confidence': confidence_score,
            'structured_analysis': structured_analysis  # NEW: Pre-parsed structured data
        }
        
        # Generate event ID
        event_id = str(uuid.uuid4())
        
        # Detect portfolio actions BEFORE inserting into spine
        portfolio_action = detect_portfolio_actions(conversation_context, user_command)
        
        # Insert into database (spine)
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO events (
                event_id, ts_event, event_type, category, session_id, 
                event_key, sequence_num, topic, symbols, confidence_score, payload
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            event_id,
            datetime.now(timezone.utc),
            event_type,
            category,
            session_id,
            event_key,
            sequence_num,
            topic,
            symbols,
            confidence_score,
            json.dumps(payload)
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Update portfolio ribs if portfolio action detected
        ribs_updated = False
        if portfolio_action:
            ribs_updated = update_portfolio_ribs(portfolio_action, event_id, db_config)
        
        # Generate summary
        base_summary = f"Stored {event_type}/{category} for topic '{topic}' (confidence: {confidence_score:.2f})"
        if portfolio_action and ribs_updated:
            summary = f"{base_summary} + Updated portfolio ribs ({portfolio_action['type']})"
        else:
            summary = base_summary
        
        return {
            'success': True,
            'event_id': event_id,
            'event_key': event_key,
            'event_type': event_type,
            'category': category,
            'topic': topic,
            'symbols_captured': symbols,
            'summary': summary,
            'confidence_score': confidence_score,
            'portfolio_action_detected': portfolio_action is not None,
            'ribs_updated': ribs_updated
        }
        
    except Exception as e:
        console.print(f"Error emitting event: {e}", style="red")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Main CLI interface for event emission."""
    parser = argparse.ArgumentParser(description='Emit unified events to MVP3 memory system')
    parser.add_argument('--user-command', required=True, help='User command (e.g., "push this")')
    parser.add_argument('--session-id', required=True, help='Session ID for conversation context')
    parser.add_argument('--context-file', help='JSON file with conversation context')
    parser.add_argument('--type-hint', help='Event type hint (analysis/proposal/insight/observation)')
    parser.add_argument('--symbols', nargs='+', help='Override symbols to store')
    parser.add_argument('--data-version', default='v1', help='Data version (default: v1)')
    parser.add_argument('--json', action='store_true', help='Output JSON response')
    
    args = parser.parse_args()
    
    # Load environment
    load_dotenv()
    
    # Get database configuration
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        console.print("DATABASE_URL not found in environment", style="red")
        sys.exit(1)
    
    try:
        db_config = parse_database_url(database_url)
    except ValueError as e:
        console.print(f"Invalid DATABASE_URL: {e}", style="red")
        sys.exit(1)
    
    # Load conversation context
    context = {}
    if args.context_file:
        try:
            with open(args.context_file, 'r') as f:
                context = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            console.print(f"Error loading context file: {e}", style="red")
            sys.exit(1)
    
    # Emit event
    result = emit_event(
        user_command=args.user_command,
        conversation_context=context,
        session_id=args.session_id,
        data_version=args.data_version,
        type_hint=args.type_hint,
        symbol_override=args.symbols,
        db_config=db_config
    )
    
    # Output result
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result['success']:
            console.print(f"✅ {result['summary']}", style="green")
            console.print(f"Event ID: {result['event_id']}")
            console.print(f"Event Key: {result['event_key']}")
        else:
            console.print(f"❌ Failed to emit event: {result['error']}", style="red")
            sys.exit(1)

if __name__ == "__main__":
    main()