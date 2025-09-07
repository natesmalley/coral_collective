"""
Unit tests for CoralCollective ProjectManager

Tests cover:
1. Project creation and initialization
2. Project loading and saving operations
3. Project status management and updates  
4. Agent interaction tracking
5. Phase management and progression
6. Metrics calculation and reporting
7. Project export functionality
8. Note management
9. Error handling and edge cases
"""

import pytest
import yaml
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from typing import Dict, List

# Import the module under test
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from project_manager import ProjectManager


class TestProjectManagerInitialization:
    """Test ProjectManager initialization and setup"""
    
    def test_initialization(self, temp_project_dir):
        """Test ProjectManager initialization"""
        
        with patch('project_manager.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            mock_path.__file__ = str(temp_project_dir / "project_manager.py")
            
            manager = ProjectManager()
            
            assert manager.base_path == temp_project_dir
            assert manager.projects_dir == temp_project_dir / "projects"
            assert isinstance(manager.active_projects, dict)
            
    def test_projects_directory_creation(self, temp_project_dir):
        """Test that projects directory is created if it doesn't exist"""
        
        with patch('project_manager.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            
            # Directory should be created
            assert manager.projects_dir.exists()
            
    def test_load_projects_empty_directory(self, temp_project_dir):
        """Test loading projects from empty directory"""
        
        with patch('project_manager.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            
            assert manager.active_projects == {}
            
    def test_load_projects_with_existing_files(self, temp_project_dir):
        """Test loading projects from directory with existing files"""
        
        # Create sample project files
        projects_dir = temp_project_dir / "projects"
        projects_dir.mkdir()
        
        sample_project1 = {
            'name': 'Test Project 1',
            'description': 'First test project',
            'status': 'active',
            'created': datetime.now().isoformat()
        }
        
        sample_project2 = {
            'name': 'Test Project 2', 
            'description': 'Second test project',
            'status': 'completed',
            'created': (datetime.now() - timedelta(days=1)).isoformat()
        }
        
        with open(projects_dir / "test_project_1.yaml", 'w') as f:
            yaml.dump(sample_project1, f)
            
        with open(projects_dir / "test_project_2.yaml", 'w') as f:
            yaml.dump(sample_project2, f)
        
        with patch('project_manager.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            
            assert len(manager.active_projects) == 2
            assert 'Test Project 1' in manager.active_projects
            assert 'Test Project 2' in manager.active_projects
            assert manager.active_projects['Test Project 1']['status'] == 'active'


class TestProjectCreation:
    """Test project creation functionality"""
    
    def test_create_project_structure(self, temp_project_dir):
        """Test the structure of created projects"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.Prompt') as mock_prompt, \
             patch('project_manager.Confirm') as mock_confirm:
            
            mock_path.return_value.parent = temp_project_dir
            
            # Mock user inputs
            mock_prompt.ask.side_effect = [
                'Test Project',           # name
                'A test project',         # description  
                '1',                      # project type choice
                ''                        # repository (optional)
            ]
            mock_confirm.ask.return_value = False  # Don't add requirements
            
            manager = ProjectManager()
            project = manager.create_project()
            
            # Verify project structure
            assert project['name'] == 'Test Project'
            assert project['description'] == 'A test project'
            assert project['type'] == 'Full-Stack Web Application'
            assert project['status'] == 'planning'
            assert project['current_phase'] == 1
            assert 'phases' in project
            assert len(project['phases']) == 4
            assert 'agents_used' in project
            assert 'tasks_completed' in project
            assert 'metrics' in project
            assert 'created' in project
            
    def test_create_project_with_requirements(self, temp_project_dir):
        """Test creating project with requirements"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.Prompt') as mock_prompt, \
             patch('project_manager.Confirm') as mock_confirm:
            
            mock_path.return_value.parent = temp_project_dir
            
            # Mock user inputs for requirements
            mock_prompt.ask.side_effect = [
                'Test Project with Reqs',
                'A test project with requirements',
                '2',  # AI-Powered Application
                'User authentication',   # requirement 1
                'Real-time chat',       # requirement 2
                '',                     # empty to finish requirements
                ''                      # repository
            ]
            mock_confirm.ask.return_value = True  # Add requirements
            
            manager = ProjectManager()
            project = manager.create_project()
            
            assert 'requirements' in project
            assert len(project['requirements']) == 2
            assert 'User authentication' in project['requirements']
            assert 'Real-time chat' in project['requirements']
            
    def test_save_project(self, temp_project_dir):
        """Test saving project to file"""
        
        with patch('project_manager.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            
            project = {
                'name': 'Test Save Project',
                'description': 'Testing save functionality',
                'status': 'active',
                'created': datetime.now().isoformat()
            }
            
            manager.save_project(project)
            
            # Verify file was created
            expected_file = manager.projects_dir / "test_save_project.yaml"
            assert expected_file.exists()
            
            # Verify content
            with open(expected_file, 'r') as f:
                saved_project = yaml.safe_load(f)
                
            assert saved_project['name'] == 'Test Save Project'
            assert saved_project['status'] == 'active'


class TestProjectManagement:
    """Test project management operations"""
    
    def setup_method(self):
        """Set up test project data"""
        self.sample_project = {
            'name': 'Test Project',
            'description': 'A test project',
            'type': 'Full-Stack Web Application',
            'created': datetime.now().isoformat(),
            'status': 'active',
            'current_phase': 1,
            'phases': {
                1: {'name': 'Planning & Foundation', 'status': 'active', 'agents': []},
                2: {'name': 'Development', 'status': 'pending', 'agents': []},
                3: {'name': 'Quality & Deployment', 'status': 'pending', 'agents': []},
                4: {'name': 'Documentation', 'status': 'pending', 'agents': []}
            },
            'agents_used': [],
            'tasks_completed': [],
            'metrics': {
                'total_time': 0,
                'success_rate': 0,
                'satisfaction': []
            },
            'notes': [],
            'repository': '',
            'deployment_url': ''
        }
    
    def test_update_project_status_valid(self, temp_project_dir):
        """Test updating project status with valid status"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console') as mock_console:
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.active_projects['Test Project'] = self.sample_project.copy()
            
            with patch.object(manager, 'save_project') as mock_save:
                manager.update_project_status('Test Project', 'paused')
                
                assert manager.active_projects['Test Project']['status'] == 'paused'
                mock_save.assert_called_once()
                mock_console.print.assert_called_with("[green]✓ Project status updated to 'paused'[/green]")
                
    def test_update_project_status_invalid(self, temp_project_dir):
        """Test updating project status with invalid status"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console') as mock_console:
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.active_projects['Test Project'] = self.sample_project.copy()
            
            manager.update_project_status('Test Project', 'invalid_status')
            
            # Status should remain unchanged
            assert manager.active_projects['Test Project']['status'] == 'active'
            mock_console.print.assert_called_with(
                "[red]Invalid status. Choose from: planning, active, paused, completed, archived[/red]"
            )
            
    def test_update_project_status_nonexistent(self, temp_project_dir):
        """Test updating status for nonexistent project"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console') as mock_console:
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.update_project_status('Nonexistent Project', 'active')
            
            mock_console.print.assert_called_with("[red]Project 'Nonexistent Project' not found![/red]")
            
    def test_add_agent_interaction(self, temp_project_dir):
        """Test adding agent interaction to project"""
        
        with patch('project_manager.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.active_projects['Test Project'] = self.sample_project.copy()
            
            with patch.object(manager, 'save_project') as mock_save:
                manager.add_agent_interaction(
                    'Test Project',
                    'backend_developer',
                    'Create REST API',
                    True,
                    8,
                    45
                )
                
                project = manager.active_projects['Test Project']
                
                # Check that interaction was added
                assert len(project['agents_used']) == 1
                interaction = project['agents_used'][0]
                assert interaction['agent'] == 'backend_developer'
                assert interaction['task'] == 'Create REST API'
                assert interaction['success'] is True
                assert interaction['satisfaction'] == 8
                assert interaction['completion_time'] == 45
                
                # Check metrics were updated
                assert project['metrics']['total_time'] == 45
                assert project['metrics']['satisfaction'] == [8]
                assert project['metrics']['success_rate'] == 100
                
                # Check current phase was updated
                assert 'backend_developer' in project['phases'][1]['agents']
                
                mock_save.assert_called_once()
                
    def test_add_multiple_agent_interactions(self, temp_project_dir):
        """Test adding multiple agent interactions and metrics calculation"""
        
        with patch('project_manager.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.active_projects['Test Project'] = self.sample_project.copy()
            
            with patch.object(manager, 'save_project'):
                # Add first interaction (successful)
                manager.add_agent_interaction(
                    'Test Project', 'backend_developer', 'Create API', True, 8, 30
                )
                
                # Add second interaction (successful)
                manager.add_agent_interaction(
                    'Test Project', 'frontend_developer', 'Create UI', True, 9, 45
                )
                
                # Add third interaction (failed)
                manager.add_agent_interaction(
                    'Test Project', 'qa_testing', 'Run tests', False, 5, 20
                )
                
                project = manager.active_projects['Test Project']
                
                # Check metrics
                assert project['metrics']['total_time'] == 95  # 30 + 45 + 20
                assert project['metrics']['satisfaction'] == [8, 9, 5]
                assert project['metrics']['success_rate'] == 66  # 2/3 * 100, rounded
                assert len(project['agents_used']) == 3
                
    def test_advance_phase(self, temp_project_dir):
        """Test advancing project to next phase"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console') as mock_console:
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.active_projects['Test Project'] = self.sample_project.copy()
            
            with patch.object(manager, 'save_project') as mock_save:
                manager.advance_phase('Test Project')
                
                project = manager.active_projects['Test Project']
                
                # Check phase advancement
                assert project['current_phase'] == 2
                assert project['phases'][1]['status'] == 'completed'
                assert project['phases'][2]['status'] == 'active'
                
                mock_save.assert_called_once()
                mock_console.print.assert_called_with("[green]✓ Advanced to Phase 2[/green]")
                
    def test_advance_phase_completion(self, temp_project_dir):
        """Test advancing from final phase completes project"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console') as mock_console:
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            project = self.sample_project.copy()
            project['current_phase'] = 4  # Final phase
            manager.active_projects['Test Project'] = project
            
            with patch.object(manager, 'save_project') as mock_save:
                manager.advance_phase('Test Project')
                
                project = manager.active_projects['Test Project']
                
                # Check project completion
                assert project['status'] == 'completed'
                assert project['phases'][4]['status'] == 'completed'
                
                mock_console.print.assert_called_with("[green]✓ Project completed![/green]")
                
    def test_add_note(self, temp_project_dir):
        """Test adding note to project"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console') as mock_console:
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.active_projects['Test Project'] = self.sample_project.copy()
            
            with patch.object(manager, 'save_project') as mock_save:
                manager.add_note('Test Project', 'This is a test note')
                
                project = manager.active_projects['Test Project']
                
                assert len(project['notes']) == 1
                note = project['notes'][0]
                assert note['text'] == 'This is a test note'
                assert 'date' in note
                
                mock_save.assert_called_once()
                mock_console.print.assert_called_with("[green]✓ Note added to project[/green]")


class TestProjectReporting:
    """Test project reporting and export functionality"""
    
    def setup_method(self):
        """Set up test project with data"""
        self.test_project = {
            'name': 'Reporting Test Project',
            'description': 'A project for testing reporting',
            'type': 'Full-Stack Web Application',
            'created': '2024-01-01T10:00:00',
            'status': 'active',
            'current_phase': 2,
            'phases': {
                1: {'name': 'Planning & Foundation', 'status': 'completed', 'agents': ['project_architect']},
                2: {'name': 'Development', 'status': 'active', 'agents': ['backend_developer']},
                3: {'name': 'Quality & Deployment', 'status': 'pending', 'agents': []},
                4: {'name': 'Documentation', 'status': 'pending', 'agents': []}
            },
            'requirements': ['User authentication', 'Real-time features'],
            'agents_used': [
                {
                    'agent': 'project_architect',
                    'task': 'Design system architecture',
                    'success': True,
                    'satisfaction': 9,
                    'completion_time': 60,
                    'timestamp': '2024-01-01T11:00:00'
                },
                {
                    'agent': 'backend_developer', 
                    'task': 'Create REST API endpoints',
                    'success': True,
                    'satisfaction': 8,
                    'completion_time': 90,
                    'timestamp': '2024-01-01T12:30:00'
                }
            ],
            'metrics': {
                'total_time': 150,
                'success_rate': 100,
                'satisfaction': [9, 8]
            },
            'notes': [
                {'date': '2024-01-01T13:00:00', 'text': 'Architecture phase completed successfully'},
                {'date': '2024-01-01T14:00:00', 'text': 'Starting API development'}
            ],
            'repository': 'https://github.com/test/reporting-project'
        }
    
    def test_generate_project_report(self, temp_project_dir):
        """Test generating comprehensive project report"""
        
        with patch('project_manager.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.active_projects['Reporting Test Project'] = self.test_project
            
            report = manager.generate_project_report('Reporting Test Project')
            
            # Check report content
            assert '# Project Report: Reporting Test Project' in report
            assert '## Overview' in report
            assert 'Full-Stack Web Application' in report
            assert '## Requirements' in report
            assert 'User authentication' in report
            assert 'Real-time features' in report
            assert '## Phase Progress' in report
            assert '✅ Phase 1: Planning & Foundation' in report
            assert '⏳ Phase 2: Development' in report
            assert '## Metrics' in report
            assert 'Total Time**: 150 minutes' in report
            assert 'Success Rate**: 100%' in report
            assert 'Average Satisfaction**: 8.5/10' in report
            assert '## Agent Activity Log' in report
            assert 'project_architect' in report
            assert 'backend_developer' in report
            assert '## Notes' in report
            assert 'Architecture phase completed' in report
            
    def test_generate_report_nonexistent_project(self, temp_project_dir):
        """Test generating report for nonexistent project"""
        
        with patch('project_manager.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            
            report = manager.generate_project_report('Nonexistent Project')
            
            assert report == "Project not found"
            
    def test_export_project_yaml(self, temp_project_dir):
        """Test exporting project in YAML format"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console') as mock_console:
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.active_projects['Test Export'] = self.test_project.copy()
            
            # Create exports directory
            exports_dir = temp_project_dir / 'exports'
            exports_dir.mkdir()
            
            manager.export_project('Test Export', 'yaml')
            
            # Check that file was created
            yaml_files = list(exports_dir.glob('*.yaml'))
            assert len(yaml_files) == 1
            
            # Verify content
            with open(yaml_files[0], 'r') as f:
                exported_data = yaml.safe_load(f)
            
            assert exported_data['name'] == 'Reporting Test Project'
            assert exported_data['type'] == 'Full-Stack Web Application'
            
            mock_console.print.assert_called()
            
    def test_export_project_json(self, temp_project_dir):
        """Test exporting project in JSON format"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console') as mock_console:
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.active_projects['Test Export JSON'] = self.test_project.copy()
            
            # Create exports directory
            exports_dir = temp_project_dir / 'exports'
            exports_dir.mkdir()
            
            manager.export_project('Test Export JSON', 'json')
            
            # Check that file was created
            json_files = list(exports_dir.glob('*.json'))
            assert len(json_files) == 1
            
            # Verify content
            with open(json_files[0], 'r') as f:
                exported_data = json.load(f)
            
            assert exported_data['name'] == 'Reporting Test Project'
            assert exported_data['type'] == 'Full-Stack Web Application'
            
    def test_export_project_markdown(self, temp_project_dir):
        """Test exporting project in Markdown format"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console') as mock_console:
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.active_projects['Test Export MD'] = self.test_project.copy()
            
            # Create exports directory
            exports_dir = temp_project_dir / 'exports'
            exports_dir.mkdir()
            
            manager.export_project('Test Export MD', 'markdown')
            
            # Check that file was created
            md_files = list(exports_dir.glob('*.md'))
            assert len(md_files) == 1
            
            # Verify content
            with open(md_files[0], 'r') as f:
                content = f.read()
            
            assert '# Project Report: Reporting Test Project' in content
            assert '## Overview' in content
            assert '## Metrics' in content
            
    def test_export_nonexistent_project(self, temp_project_dir):
        """Test exporting nonexistent project"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console') as mock_console:
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.export_project('Nonexistent Project', 'yaml')
            
            mock_console.print.assert_called_with("[red]Project 'Nonexistent Project' not found![/red]")


class TestProjectListing:
    """Test project listing and display functionality"""
    
    def test_list_projects_empty(self, temp_project_dir):
        """Test listing projects when no projects exist"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console') as mock_console:
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.list_projects()
            
            mock_console.print.assert_called_with("[yellow]No projects found. Create one first![/yellow]")
            
    def test_list_projects_with_data(self, temp_project_dir):
        """Test listing projects with existing data"""
        
        projects = {
            'Project A': {
                'name': 'Project A',
                'type': 'Web App',
                'status': 'active',
                'current_phase': 1,
                'phases': {1: {'name': 'Planning'}},
                'agents_used': [],
                'created': '2024-01-01T10:00:00'
            },
            'Project B': {
                'name': 'Project B', 
                'type': 'API Service',
                'status': 'completed',
                'current_phase': 4,
                'phases': {4: {'name': 'Documentation'}},
                'agents_used': [{'agent': 'backend_dev'}],
                'created': '2024-01-02T10:00:00'
            }
        }
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console') as mock_console:
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.active_projects = projects
            
            manager.list_projects()
            
            # Console should be called with a table
            mock_console.print.assert_called()
            
    def test_list_projects_with_status_filter(self, temp_project_dir):
        """Test listing projects with status filter"""
        
        projects = {
            'Active Project': {
                'name': 'Active Project',
                'status': 'active',
                'type': 'Web App',
                'current_phase': 1,
                'phases': {1: {'name': 'Planning'}},
                'agents_used': [],
                'created': '2024-01-01T10:00:00'
            },
            'Completed Project': {
                'name': 'Completed Project',
                'status': 'completed', 
                'type': 'API',
                'current_phase': 4,
                'phases': {4: {'name': 'Done'}},
                'agents_used': [],
                'created': '2024-01-02T10:00:00'
            }
        }
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console') as mock_console:
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.active_projects = projects
            
            manager.list_projects(status_filter='active')
            
            # Should display table (specific content testing would require more complex mocking)
            mock_console.print.assert_called()
            
    def test_show_project_details(self, temp_project_dir):
        """Test showing detailed project information"""
        
        project = {
            'name': 'Detail Test Project',
            'type': 'Full-Stack App',
            'status': 'active',
            'created': '2024-01-01T10:00:00.123456',
            'current_phase': 2,
            'phases': {
                1: {'name': 'Planning', 'status': 'completed', 'agents': ['architect']},
                2: {'name': 'Development', 'status': 'active', 'agents': ['backend_dev']},
                3: {'name': 'Testing', 'status': 'pending', 'agents': []},
                4: {'name': 'Deployment', 'status': 'pending', 'agents': []}
            },
            'requirements': ['Auth system', 'Real-time chat'],
            'agents_used': [
                {'agent': 'architect', 'task': 'Design system'},
                {'agent': 'backend_dev', 'task': 'Create API'}
            ],
            'metrics': {
                'total_time': 120,
                'success_rate': 100,
                'satisfaction': [8, 9]
            },
            'notes': [
                {'date': '2024-01-01T11:00:00', 'text': 'Started project planning'},
                {'date': '2024-01-01T12:00:00', 'text': 'Architecture approved'}
            ],
            'repository': 'https://github.com/test/project'
        }
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console') as mock_console:
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.active_projects['Detail Test Project'] = project
            
            manager.show_project_details('Detail Test Project')
            
            # Should display detailed project information
            mock_console.print.assert_called()
            
    def test_show_project_details_nonexistent(self, temp_project_dir):
        """Test showing details for nonexistent project"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console') as mock_console:
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            manager.show_project_details('Nonexistent Project')
            
            mock_console.print.assert_called_with("[red]Project 'Nonexistent Project' not found![/red]")


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_add_agent_interaction_nonexistent_project(self, temp_project_dir):
        """Test adding agent interaction to nonexistent project"""
        
        with patch('project_manager.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            
            # Should not raise exception, just return silently
            manager.add_agent_interaction(
                'Nonexistent Project',
                'test_agent',
                'test_task',
                True,
                8,
                30
            )
            
            # No projects should exist
            assert len(manager.active_projects) == 0
            
    def test_advance_phase_nonexistent_project(self, temp_project_dir):
        """Test advancing phase for nonexistent project"""
        
        with patch('project_manager.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            
            # Should not raise exception, just return silently
            manager.advance_phase('Nonexistent Project')
            
            assert len(manager.active_projects) == 0
            
    def test_add_note_nonexistent_project(self, temp_project_dir):
        """Test adding note to nonexistent project"""
        
        with patch('project_manager.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            
            # Should not raise exception, just return silently
            manager.add_note('Nonexistent Project', 'Test note')
            
            assert len(manager.active_projects) == 0
            
    def test_add_note_to_project_without_notes_field(self, temp_project_dir):
        """Test adding note to project that doesn't have notes field"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console'):
            
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            
            # Create project without notes field
            project = {
                'name': 'Project Without Notes',
                'status': 'active'
            }
            manager.active_projects['Project Without Notes'] = project
            
            with patch.object(manager, 'save_project'):
                manager.add_note('Project Without Notes', 'First note')
                
                # Should create notes field
                assert 'notes' in manager.active_projects['Project Without Notes']
                assert len(manager.active_projects['Project Without Notes']['notes']) == 1


class TestMetricsCalculation:
    """Test metrics calculation and aggregation"""
    
    def test_success_rate_calculation_edge_cases(self, temp_project_dir):
        """Test success rate calculation with edge cases"""
        
        with patch('project_manager.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            
            project = {
                'name': 'Metrics Test',
                'current_phase': 1,
                'phases': {1: {'agents': []}},
                'agents_used': [],
                'metrics': {
                    'total_time': 0,
                    'success_rate': 0,
                    'satisfaction': []
                }
            }
            
            manager.active_projects['Metrics Test'] = project
            
            with patch.object(manager, 'save_project'):
                # Test with all successful interactions
                manager.add_agent_interaction('Metrics Test', 'agent1', 'task1', True, 8, 30)
                manager.add_agent_interaction('Metrics Test', 'agent2', 'task2', True, 9, 40)
                manager.add_agent_interaction('Metrics Test', 'agent3', 'task3', True, 7, 35)
                
                assert manager.active_projects['Metrics Test']['metrics']['success_rate'] == 100
                
                # Add one failed interaction
                manager.add_agent_interaction('Metrics Test', 'agent4', 'task4', False, 4, 25)
                
                # Should be 75% (3 out of 4 successful)
                assert manager.active_projects['Metrics Test']['metrics']['success_rate'] == 75
                
    def test_satisfaction_tracking(self, temp_project_dir):
        """Test satisfaction score tracking"""
        
        with patch('project_manager.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            
            manager = ProjectManager()
            
            project = {
                'name': 'Satisfaction Test',
                'current_phase': 1,
                'phases': {1: {'agents': []}},
                'agents_used': [],
                'metrics': {
                    'total_time': 0,
                    'success_rate': 0,
                    'satisfaction': []
                }
            }
            
            manager.active_projects['Satisfaction Test'] = project
            
            with patch.object(manager, 'save_project'):
                manager.add_agent_interaction('Satisfaction Test', 'agent1', 'task1', True, 8, 30)
                manager.add_agent_interaction('Satisfaction Test', 'agent2', 'task2', True, 6, 40)
                manager.add_agent_interaction('Satisfaction Test', 'agent3', 'task3', True, 10, 35)
                
                satisfaction_scores = manager.active_projects['Satisfaction Test']['metrics']['satisfaction']
                
                assert satisfaction_scores == [8, 6, 10]
                assert sum(satisfaction_scores) / len(satisfaction_scores) == 8.0  # Average


# Integration test for complete project lifecycle
@pytest.mark.integration
class TestProjectLifecycle:
    """Integration tests for complete project lifecycle"""
    
    def test_complete_project_workflow(self, temp_project_dir):
        """Test complete project workflow from creation to completion"""
        
        with patch('project_manager.Path') as mock_path, \
             patch('project_manager.console'), \
             patch('project_manager.Prompt') as mock_prompt, \
             patch('project_manager.Confirm') as mock_confirm:
            
            mock_path.return_value.parent = temp_project_dir
            
            # Mock project creation inputs
            mock_prompt.ask.side_effect = [
                'Integration Test Project',
                'Testing complete workflow',
                '1',  # Full-Stack Web Application
                ''    # No repository
            ]
            mock_confirm.ask.return_value = False
            
            manager = ProjectManager()
            
            # 1. Create project
            project = manager.create_project()
            assert project['name'] == 'Integration Test Project'
            assert project['status'] == 'planning'
            assert project['current_phase'] == 1
            
            # 2. Add agent interactions for Phase 1
            manager.add_agent_interaction(
                'Integration Test Project', 'project_architect', 'Design architecture', True, 9, 60
            )
            
            # 3. Advance to Phase 2
            manager.advance_phase('Integration Test Project')
            project = manager.active_projects['Integration Test Project']
            assert project['current_phase'] == 2
            assert project['phases'][1]['status'] == 'completed'
            
            # 4. Add agent interactions for Phase 2
            manager.add_agent_interaction(
                'Integration Test Project', 'backend_developer', 'Create API', True, 8, 90
            )
            manager.add_agent_interaction(
                'Integration Test Project', 'frontend_developer', 'Create UI', True, 7, 75
            )
            
            # 5. Add a note
            manager.add_note('Integration Test Project', 'Development phase going well')
            
            # 6. Check metrics
            project = manager.active_projects['Integration Test Project']
            assert project['metrics']['total_time'] == 225  # 60 + 90 + 75
            assert project['metrics']['success_rate'] == 100
            assert len(project['metrics']['satisfaction']) == 3
            assert len(project['notes']) == 1
            
            # 7. Generate and verify report
            report = manager.generate_project_report('Integration Test Project')
            assert 'Integration Test Project' in report
            assert 'project_architect' in report
            assert 'backend_developer' in report
            assert 'frontend_developer' in report
            
            # 8. Continue through remaining phases
            manager.advance_phase('Integration Test Project')  # Phase 3
            manager.advance_phase('Integration Test Project')  # Phase 4
            manager.advance_phase('Integration Test Project')  # Complete project
            
            project = manager.active_projects['Integration Test Project']
            assert project['status'] == 'completed'
            assert project['current_phase'] == 4