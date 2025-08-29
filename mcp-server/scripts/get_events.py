#!/usr/bin/env python3
"""
MVP3 Event Retrieval Script - Unified Memory Retrieval
Handles searching, filtering, and retrieving stored events.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv

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

def format_age(timestamp: datetime) -> str:
    """Format event age in human-readable format."""
    now = datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    else:
        return "just now"

def calculate_age_hours(timestamp: datetime) -> float:
    """Calculate event age in hours."""
    now = datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    diff = now - timestamp
    return diff.total_seconds() / 3600.0

def build_query_conditions(filters: Dict[str, Any]) -> Tuple[str, List[Any]]:
    """Build WHERE clause conditions and parameters."""
    conditions = []
    params = []
    param_count = 0
    
    # Event key filter
    if filters.get('event_key'):
        param_count += 1
        conditions.append(f"event_key = %s")
        params.append(filters['event_key'])
    
    # Event ID filter
    if filters.get('event_id'):
        param_count += 1
        conditions.append(f"event_id = %s")
        params.append(filters['event_id'])
    
    # Topic filter
    if filters.get('topic'):
        param_count += 1
        conditions.append(f"topic = %s")
        params.append(filters['topic'])
    
    # Symbols filter (still available for granular filtering)
    if filters.get('symbols'):
        param_count += 1
        conditions.append(f"symbols && %s")
        params.append(filters['symbols'])
    
    # Event types filter
    if filters.get('event_types'):
        param_count += 1
        conditions.append(f"event_type = ANY(%s)")
        params.append(filters['event_types'])
    
    # Categories filter
    if filters.get('categories'):
        param_count += 1
        conditions.append(f"category = ANY(%s)")
        params.append(filters['categories'])
    
    # Minimum confidence filter
    if filters.get('min_confidence'):
        param_count += 1
        conditions.append(f"confidence_score >= %s")
        params.append(filters['min_confidence'])
    
    # Time window filter
    if filters.get('hours_back'):
        param_count += 1
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=filters['hours_back'])
        conditions.append(f"ts_event >= %s")
        params.append(cutoff_time)
    
    # Session ID filter
    if filters.get('session_id'):
        param_count += 1
        conditions.append(f"session_id = %s")
        params.append(filters['session_id'])
    
    # Referenced events filter
    if filters.get('referenced_events'):
        param_count += 1
        conditions.append(f"cross_references && %s")
        params.append(filters['referenced_events'])
    
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    return where_clause, params

def build_order_clause(sort_by: str) -> str:
    """Build ORDER BY clause."""
    if sort_by == 'confidence':
        return " ORDER BY confidence_score DESC, ts_event DESC"
    elif sort_by == 'relevance':
        # For now, relevance is confidence + recency
        return " ORDER BY (confidence_score * 0.7 + EXTRACT(EPOCH FROM (NOW() - ts_event))/86400.0 * -0.3) DESC"
    else:  # timestamp (default)
        return " ORDER BY ts_event DESC"

def get_events(
    event_key: str = None,
    event_id: str = None,
    filters: Dict[str, Any] = None,
    limit: int = 10,
    sort_by: str = 'timestamp',
    include_cross_references: bool = False,
    db_config: dict = None
) -> Dict[str, Any]:
    """Get events from the database with filtering and sorting."""
    
    if filters is None:
        filters = {}
    
    # Add specific filters to general filters dict
    if event_key:
        filters['event_key'] = event_key
    if event_id:
        filters['event_id'] = event_id
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build query
        base_query = """
            SELECT 
                event_id,
                event_key,
                event_type,
                category,
                session_id,
                sequence_num,
                topic,
                symbols,
                confidence_score,
                ts_event,
                ts_recorded,
                payload,
                cross_references,
                labels
            FROM events
        """
        
        # Add WHERE conditions
        where_clause, params = build_query_conditions(filters)
        
        # Add ORDER BY
        order_clause = build_order_clause(sort_by)
        
        # Add LIMIT
        limit_clause = f" LIMIT {min(limit, 50)}"  # Cap at 50
        
        # Execute query
        full_query = base_query + where_clause + order_clause + limit_clause
        cursor.execute(full_query, params)
        rows = cursor.fetchall()
        
        # Get total count (without limit)
        count_query = "SELECT COUNT(*) as total FROM events" + where_clause
        cursor.execute(count_query, params)
        count_result = cursor.fetchone()
        total_found = count_result['total'] if count_result else 0
        
        # Process results
        events = []
        for row in rows:
            # Parse payload (JSONB column returns dict directly)
            payload = row['payload'] if row['payload'] else {}
            
            # Calculate age
            age_hours = calculate_age_hours(row['ts_event'])
            
            # Build event record
            event_record = {
                'event_id': row['event_id'],
                'event_key': row['event_key'],
                'event_type': row['event_type'],
                'category': row['category'],
                'topic': row['topic'],
                'symbols': row['symbols'],
                'confidence_score': float(row['confidence_score']) if row['confidence_score'] else 0.0,
                'stored_at': row['ts_event'].isoformat(),
                'age_hours': age_hours,
                'sequence_num': row['sequence_num']
            }
            
            # Add summary from payload
            if payload.get('agent_reasoning'):
                # Create summary from first sentence of reasoning
                reasoning = payload['agent_reasoning']
                first_sentence = reasoning.split('.')[0][:200]
                event_record['summary'] = first_sentence + ('...' if len(reasoning) > 200 else '')
            else:
                event_record['summary'] = f"{row['event_type']} event for {', '.join(row['symbols'] or [])}"
            
            # Add optional fields based on request
            if include_cross_references:
                event_record['cross_references'] = row['cross_references'] or []
            
            # Add agent reasoning and parameters if available
            if payload.get('agent_reasoning'):
                event_record['agent_reasoning'] = payload['agent_reasoning']
            if payload.get('parameters'):
                event_record['parameters'] = payload['parameters']
            
            events.append(event_record)
        
        cursor.close()
        conn.close()
        
        return {
            'events': events,
            'total_found': total_found,
            'filters_applied': filters,
            'sort_by': sort_by,
            'limit_applied': min(limit, 50)
        }
        
    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {e}"
        if hasattr(e, 'pgcode'):
            error_msg += f" (PG Code: {e.pgcode})"
        console.print(f"Error retrieving events: {error_msg}", style="red")
        console.print(f"Full traceback: {traceback.format_exc()}", style="dim")
        return {
            'events': [],
            'total_found': 0,
            'error': error_msg
        }

def display_events_table(events: List[Dict], title: str = "Events"):
    """Display events in a rich table format."""
    if not events:
        console.print("No events found", style="yellow")
        return
    
    table = Table(title=title, show_header=True, header_style="bold magenta")
    
    table.add_column("Age", style="dim", width=8)
    table.add_column("Type/Category", width=20)
    table.add_column("Topic", style="cyan", width=15)
    table.add_column("Confidence", justify="right", width=10)
    table.add_column("Summary", width=45)
    table.add_column("ID", style="dim", width=8)
    
    for event in events:
        age_str = format_age(datetime.fromisoformat(event['stored_at'].replace('Z', '+00:00')))
        type_category = f"{event['event_type']}/{event['category']}"
        topic_str = event.get('topic', 'N/A')[:14] + ('...' if len(event.get('topic', '')) > 15 else '')
        confidence_str = f"{event['confidence_score']:.2f}" if event.get('confidence_score') else "N/A"
        summary = event.get('summary', '')[:42] + ('...' if len(event.get('summary', '')) > 45 else '')
        event_id_short = event['event_id'][:8]
        
        table.add_row(
            age_str,
            type_category,
            topic_str,
            confidence_str,
            summary,
            event_id_short
        )
    
    console.print(table)

def display_event_details(event: Dict):
    """Display detailed information about a single event."""
    symbols_str = ', '.join(event.get('symbols', [])) or 'None'
    age_str = format_age(datetime.fromisoformat(event['stored_at'].replace('Z', '+00:00')))
    
    details = f"""**Event Type:** {event['event_type']}/{event['category']}
**Topic:** {event.get('topic', 'N/A')}
**Symbols:** {symbols_str}
**Confidence:** {event.get('confidence_score', 'N/A')}
**Age:** {age_str}
**Event ID:** {event['event_id']}
**Event Key:** {event['event_key']}

**Summary:** {event.get('summary', 'No summary available')}"""
    
    if event.get('agent_reasoning'):
        details += f"\n\n**Agent Reasoning:**\n{event['agent_reasoning']}"
    
    if event.get('parameters'):
        params_str = ', '.join([f"{k}={v}" for k, v in event['parameters'].items()])
        details += f"\n\n**Parameters:** {params_str}"
    
    if event.get('cross_references'):
        refs_str = ', '.join(event['cross_references'])
        details += f"\n\n**Cross References:** {refs_str}"
    
    console.print(Panel(details, title="Event Details", border_style="blue"))

def main():
    """Main CLI interface for event retrieval."""
    parser = argparse.ArgumentParser(description='Retrieve events from MVP3 memory system')
    
    # Exact lookup options
    parser.add_argument('--event-key', help='Specific event by correlation key')
    parser.add_argument('--event-id', help='Specific event by UUID')
    
    # Filter options
    parser.add_argument('--topic', help='Filter by topic (e.g., SBET, market_analysis)')
    parser.add_argument('--symbols', nargs='+', help='Filter by ticker symbols')
    parser.add_argument('--types', nargs='+', help='Filter by event types', 
                       choices=['analysis', 'proposal', 'insight', 'observation'])
    parser.add_argument('--categories', nargs='+', help='Filter by categories')
    parser.add_argument('--min-confidence', type=float, help='Minimum confidence threshold (0.0-1.0)')
    parser.add_argument('--hours-back', type=int, default=168, help='Time window in hours (default: 168 = 1 week)')
    parser.add_argument('--session-id', help='Filter by specific session ID')
    parser.add_argument('--referenced-events', nargs='+', help='Events that reference these IDs')
    
    # Output control
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of results (default: 10, max: 50)')
    parser.add_argument('--sort-by', choices=['timestamp', 'confidence', 'relevance'], 
                       default='timestamp', help='Sort order (default: timestamp)')
    parser.add_argument('--include-cross-references', action='store_true', 
                       help='Include cross-reference information')
    parser.add_argument('--details', action='store_true', help='Show detailed view for single event')
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
    
    # Build filters
    filters = {}
    if args.topic:
        filters['topic'] = args.topic
    if args.symbols:
        filters['symbols'] = args.symbols
    if args.types:
        filters['event_types'] = args.types
    if args.categories:
        filters['categories'] = args.categories
    if args.min_confidence is not None:
        filters['min_confidence'] = args.min_confidence
    if args.hours_back:
        filters['hours_back'] = args.hours_back
    if args.session_id:
        filters['session_id'] = args.session_id
    if args.referenced_events:
        filters['referenced_events'] = args.referenced_events
    
    # Get events
    result = get_events(
        event_key=args.event_key,
        event_id=args.event_id,
        filters=filters,
        limit=args.limit,
        sort_by=args.sort_by,
        include_cross_references=args.include_cross_references,
        db_config=db_config
    )
    
    # Output results
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        if 'error' in result:
            console.print(f"[ERROR] Error retrieving events: {result['error']}", style="red")
            sys.exit(1)
        
        events = result['events']
        total = result['total_found']
        
        if not events:
            console.print("No events found matching the criteria", style="yellow")
            return
        
        # Show summary
        filters_applied = result.get('filters_applied', {})
        filter_info = []
        if filters_applied:
            if 'symbols' in filters_applied:
                filter_info.append(f"symbols: {', '.join(filters_applied['symbols'])}")
            if 'event_types' in filters_applied:
                filter_info.append(f"types: {', '.join(filters_applied['event_types'])}")
            if 'categories' in filters_applied:
                filter_info.append(f"categories: {', '.join(filters_applied['categories'])}")
            if 'min_confidence' in filters_applied:
                filter_info.append(f"min confidence: {filters_applied['min_confidence']}")
            if 'hours_back' in filters_applied:
                filter_info.append(f"last {filters_applied['hours_back']}h")
        
        filter_str = f" ({', '.join(filter_info)})" if filter_info else ""
        title = f"Found {len(events)} of {total} events{filter_str}"
        
        # Display results
        if args.details and len(events) == 1:
            display_event_details(events[0])
        else:
            display_events_table(events, title)
            
            if len(events) == 1:
                console.print("\n[dim]💡 Use --details flag for detailed view[/dim]")

if __name__ == "__main__":
    main()