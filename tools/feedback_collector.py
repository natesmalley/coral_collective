#!/usr/bin/env python3
"""
Agent Feedback Collector
Utility to collect and process agent feedback after interactions
"""

import yaml
import json
from datetime import datetime
from pathlib import Path
import argparse
from typing import Dict, List, Optional

class FeedbackCollector:
    def __init__(self, feedback_path: str = "feedback/agent_feedback.yaml",
                 metrics_path: str = "metrics/agent_metrics.yaml"):
        self.feedback_path = Path(feedback_path)
        self.metrics_path = Path(metrics_path)
        self.ensure_paths()
    
    def ensure_paths(self):
        """Ensure feedback and metrics directories exist"""
        self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
    
    def add_feedback(self, agent: str, issue: str, suggestion: str, 
                    priority: str = "medium", reported_by: str = "user"):
        """Add new feedback entry for an agent"""
        try:
            with open(self.feedback_path, 'r') as f:
                data = yaml.safe_load(f) or {}
        except FileNotFoundError:
            data = {"version": "1.0", "agents": {}}
        
        if 'agents' not in data:
            data['agents'] = {}
        
        if agent not in data['agents']:
            data['agents'][agent] = {"feedback": []}
        
        feedback_entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "issue": issue,
            "suggestion": suggestion,
            "priority": priority,
            "status": "pending",
            "reported_by": reported_by
        }
        
        data['agents'][agent]['feedback'].append(feedback_entry)
        data['last_updated'] = datetime.now().strftime("%Y-%m-%d")
        
        with open(self.feedback_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Feedback added for {agent}")
        return feedback_entry
    
    def record_interaction(self, agent: str, success: bool, 
                          satisfaction: int, task_type: str,
                          completion_time: int = None):
        """Record an agent interaction for metrics"""
        try:
            with open(self.metrics_path, 'r') as f:
                data = yaml.safe_load(f) or {}
        except FileNotFoundError:
            data = self.initialize_metrics()
        
        month = datetime.now().strftime("%Y-%m")
        
        if 'agent_metrics' not in data:
            data['agent_metrics'] = {}
        
        if agent not in data['agent_metrics']:
            data['agent_metrics'][agent] = {
                "current_month": self.create_empty_metrics()
            }
        
        metrics = data['agent_metrics'][agent]['current_month']
        
        # Update metrics
        metrics['total_uses'] = metrics.get('total_uses', 0) + 1
        
        # Update success rate
        successful = metrics.get('successful_tasks', 0)
        if success:
            successful += 1
        metrics['successful_tasks'] = successful
        metrics['success_rate'] = f"{(successful / metrics['total_uses']) * 100:.0f}%"
        
        # Update satisfaction
        total_satisfaction = metrics.get('total_satisfaction', 0) + satisfaction
        metrics['total_satisfaction'] = total_satisfaction
        metrics['avg_satisfaction'] = round(total_satisfaction / metrics['total_uses'], 1)
        
        # Update completion time
        if completion_time:
            total_time = metrics.get('total_completion_time', 0) + completion_time
            metrics['total_completion_time'] = total_time
            metrics['avg_completion_time'] = f"{total_time // metrics['total_uses']}min"
        
        # Track task types
        if 'tasks_completed' not in metrics:
            metrics['tasks_completed'] = {}
        
        task_key = task_type.replace(' ', '_').lower()
        metrics['tasks_completed'][task_key] = metrics['tasks_completed'].get(task_key, 0) + 1
        
        with open(self.metrics_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Interaction recorded for {agent}")
        return metrics
    
    def create_empty_metrics(self) -> Dict:
        """Create empty metrics structure"""
        return {
            "total_uses": 0,
            "success_rate": "0%",
            "avg_satisfaction": 0,
            "avg_completion_time": "0min",
            "successful_tasks": 0,
            "total_satisfaction": 0,
            "total_completion_time": 0,
            "common_issues": {},
            "strengths": {},
            "tasks_completed": {}
        }
    
    def initialize_metrics(self) -> Dict:
        """Initialize metrics file structure"""
        return {
            "version": "1.0",
            "metrics_period": "monthly",
            "current_month": datetime.now().strftime("%Y-%m"),
            "agent_metrics": {}
        }
    
    def get_agent_feedback(self, agent: str) -> List[Dict]:
        """Get all feedback for a specific agent"""
        try:
            with open(self.feedback_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if agent in data.get('agents', {}):
                return data['agents'][agent].get('feedback', [])
        except FileNotFoundError:
            pass
        
        return []
    
    def get_agent_metrics(self, agent: str) -> Dict:
        """Get metrics for a specific agent"""
        try:
            with open(self.metrics_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if agent in data.get('agent_metrics', {}):
                return data['agent_metrics'][agent]
        except FileNotFoundError:
            pass
        
        return {}
    
    def generate_report(self, agent: Optional[str] = None) -> str:
        """Generate a performance report"""
        report = []
        
        try:
            with open(self.metrics_path, 'r') as f:
                metrics_data = yaml.safe_load(f)
        except FileNotFoundError:
            return "No metrics data found"
        
        try:
            with open(self.feedback_path, 'r') as f:
                feedback_data = yaml.safe_load(f)
        except FileNotFoundError:
            feedback_data = {}
        
        if agent:
            # Single agent report
            report.append(f"# Performance Report: {agent}")
            report.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
            
            # Metrics
            if agent in metrics_data.get('agent_metrics', {}):
                m = metrics_data['agent_metrics'][agent].get('current_month', {})
                report.append("## Metrics")
                report.append(f"- Total Uses: {m.get('total_uses', 0)}")
                report.append(f"- Success Rate: {m.get('success_rate', 'N/A')}")
                report.append(f"- Avg Satisfaction: {m.get('avg_satisfaction', 'N/A')}")
                report.append(f"- Avg Completion Time: {m.get('avg_completion_time', 'N/A')}")
            
            # Feedback
            if agent in feedback_data.get('agents', {}):
                feedback = feedback_data['agents'][agent].get('feedback', [])
                pending = [f for f in feedback if f.get('status') == 'pending']
                if pending:
                    report.append("\n## Pending Improvements")
                    for f in pending:
                        report.append(f"- [{f['priority']}] {f['issue']}")
        else:
            # Overall report
            report.append("# Agent Force Performance Report")
            report.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
            
            if 'performance_summary' in metrics_data:
                s = metrics_data['performance_summary']
                report.append("## Summary")
                report.append(f"- Total Interactions: {s.get('total_interactions', 0)}")
                report.append(f"- Overall Success Rate: {s.get('overall_success_rate', 'N/A')}")
                report.append(f"- Average Satisfaction: {s.get('average_satisfaction', 'N/A')}")
                
                if 'most_used_agents' in s:
                    report.append("\n## Most Used Agents")
                    for agent_info in s['most_used_agents'][:5]:
                        report.append(f"- {agent_info}")
        
        return '\n'.join(report)

def main():
    parser = argparse.ArgumentParser(description='Agent Feedback Collector')
    parser.add_argument('action', choices=['feedback', 'interaction', 'report'],
                       help='Action to perform')
    parser.add_argument('--agent', required=False, help='Agent name')
    parser.add_argument('--issue', help='Issue description')
    parser.add_argument('--suggestion', help='Improvement suggestion')
    parser.add_argument('--priority', choices=['low', 'medium', 'high', 'critical'],
                       default='medium', help='Priority level')
    parser.add_argument('--success', action='store_true', help='Task was successful')
    parser.add_argument('--satisfaction', type=int, choices=range(1, 11),
                       help='Satisfaction score (1-10)')
    parser.add_argument('--task-type', help='Type of task performed')
    parser.add_argument('--time', type=int, help='Completion time in minutes')
    
    args = parser.parse_args()
    collector = FeedbackCollector()
    
    if args.action == 'feedback':
        if not all([args.agent, args.issue, args.suggestion]):
            print("Error: --agent, --issue, and --suggestion are required for feedback")
            return
        
        collector.add_feedback(
            args.agent,
            args.issue,
            args.suggestion,
            args.priority
        )
    
    elif args.action == 'interaction':
        if not all([args.agent, args.satisfaction, args.task_type]):
            print("Error: --agent, --satisfaction, and --task-type are required")
            return
        
        collector.record_interaction(
            args.agent,
            args.success,
            args.satisfaction,
            args.task_type,
            args.time
        )
    
    elif args.action == 'report':
        report = collector.generate_report(args.agent)
        print(report)

if __name__ == "__main__":
    main()