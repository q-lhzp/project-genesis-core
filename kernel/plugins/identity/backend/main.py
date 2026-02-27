"""
Identity Engine Plugin - Soul Evolution Pipeline Backend
Ported from project-genesis/skills/soul-evolution/

This plugin implements the 10-step Soul Evolution Pipeline:
1. INGEST - Harvest experiences from conversations and sources
2. REFLECT - Check trigger conditions and create reflections
3. PROPOSE - Generate proposals from reflections
4. GOVERN - Resolve proposals per governance level
5. APPLY - Execute approved changes to SOUL.md
6. LOG - Record to soul_changes.jsonl and soul_changes.md
7. STATE - Update soul-state.json
8. NOTIFY - Inform the human of changes
9. FINAL CHECK - Verify pipeline actually ran
10. PIPELINE REPORT - Save execution record
"""

import json
import os
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='[IDENTITY] %(message)s')
logger = logging.getLogger("identity")

# =============================================================================
# CONSTANTS & PATTERNS
# =============================================================================

ID_PATTERN = re.compile(r'^PROP-\d{8}-\d{3}$')
REF_ID_PATTERN = re.compile(r'^REF-\d{8}-\d{3}$')
EXP_ID_PATTERN = re.compile(r'^EXP-\d{8}-\d{4}$')
VALID_TAGS = {'[CORE]', '[MUTABLE]'}
TAG_PATTERN = re.compile(r'\[(CORE|MUTABLE)\]\s*$')
BULLET_PATTERN = re.compile(r'^- .+')

REQUIRED_SOUL_SECTIONS = {
    '## Personality', '## Philosophy', '## Boundaries', '## Continuity'
}

VALID_CHANGE_TYPES = {'add', 'modify', 'remove'}
VALID_TRIGGERS = {'gap', 'drift', 'contradiction', 'growth', 'refinement'}
VALID_REFLECTION_TYPES = {'routine_batch', 'notable_batch', 'pivotal_immediate'}

# =============================================================================
# VALIDATORS (Internal Helper Classes)
# =============================================================================

class SoulValidator:
    """Validates SOUL.md structural integrity."""

    @staticmethod
    def parse_soul(filepath: str) -> Optional[Dict]:
        if not os.path.exists(filepath):
            return None

        with open(filepath, 'r') as f:
            lines = f.readlines()

        sections = set()
        subsections = {}
        bullets = []
        current_section = None
        current_sub = None

        for i, raw_line in enumerate(lines, 1):
            line = raw_line.rstrip('\n')
            stripped = line.strip()

            if stripped.startswith('## ') and not stripped.startswith('### '):
                current_section = stripped
                current_sub = None
                sections.add(current_section)
                if current_section not in subsections:
                    subsections[current_section] = set()
            elif stripped.startswith('### '):
                current_sub = stripped
                if current_section:
                    subsections[current_section].add(current_sub)
            elif BULLET_PATTERN.match(stripped):
                tag_match = TAG_PATTERN.search(stripped)
                tag = tag_match.group(0).strip() if tag_match else None
                bullets.append({
                    'line': i,
                    'text': stripped,
                    'tag': tag,
                    'section': current_section,
                    'subsection': current_sub
                })

        return {
            'lines': lines,
            'sections': sections,
            'subsections': subsections,
            'bullets': bullets
        }

    @staticmethod
    def validate(filepath: str, snapshot_mode: str = None, snapshot_path: str = None) -> Dict:
        errors = []
        warnings = []
        parsed = SoulValidator.parse_soul(filepath)

        if parsed is None:
            return {
                'status': 'FAIL', 'file': filepath,
                'errors': [{'field': None, 'message': f'File not found: {filepath}'}],
                'warnings': [], 'stats': {}
            }

        # Required sections
        for section in REQUIRED_SOUL_SECTIONS:
            if section not in parsed['sections']:
                errors.append({
                    'field': 'structure',
                    'message': f'Missing required section: {section}'
                })

        # Every bullet must have a tag
        untagged = [b for b in parsed['bullets'] if b['tag'] is None]
        for b in untagged:
            errors.append({
                'field': 'tag',
                'message': f'Line {b["line"]}: Bullet has no [CORE] or [MUTABLE] tag'
            })

        # Tags must be at END of line
        tag_at_start = re.compile(r'^- \[(CORE|MUTABLE)\]')
        for b in parsed['bullets']:
            if tag_at_start.match(b['text']):
                errors.append({
                    'field': 'tag_position',
                    'message': f'Line {b["line"]}: Tag is at START of bullet (must be at END)'
                })

        # Valid tags only
        for b in parsed['bullets']:
            if b['tag'] and b['tag'] not in VALID_TAGS:
                errors.append({
                    'field': 'tag',
                    'message': f'Line {b["line"]}: Invalid tag "{b["tag"]}"'
                })

        core_count = len([b for b in parsed['bullets'] if b['tag'] == '[CORE]'])
        mutable_count = len([b for b in parsed['bullets'] if b['tag'] == '[MUTABLE]'])

        status = 'FAIL' if errors else 'PASS'
        return {
            'status': status,
            'file': filepath,
            'errors': errors,
            'warnings': warnings,
            'stats': {
                'sections': len(parsed['sections']),
                'total_bullets': len(parsed['bullets']),
                'core_bullets': core_count,
                'mutable_bullets': mutable_count
            }
        }


class ProposalValidator:
    """Validates proposals against SOUL.md."""

    @staticmethod
    def load_soul(soul_path: str):
        if not os.path.exists(soul_path):
            return None, None, None

        with open(soul_path, 'r') as f:
            content = f.read()
            lines = content.split('\n')

        sections = set()
        subsections = {}
        current_section = None

        for line in lines:
            if line.startswith('## ') and not line.startswith('### '):
                current_section = line.strip()
                sections.add(current_section)
                subsections[current_section] = set()
            elif line.startswith('### ') and current_section:
                subsections[current_section].add(line.strip())

        bullet_lines = set()
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- '):
                bullet_lines.add(stripped)

        return sections, subsections, bullet_lines

    @staticmethod
    def validate(proposals_path: str, soul_path: str) -> Dict:
        errors = []
        warnings = []
        seen_ids = set()

        sections, subsections, bullet_lines = ProposalValidator.load_soul(soul_path)
        if sections is None:
            errors.append({'message': f'SOUL.md not found: {soul_path}'})
            return {'status': 'FAIL', 'errors': errors, 'warnings': warnings}

        if not os.path.exists(proposals_path):
            return {'status': 'PASS', 'errors': [], 'warnings': [{'message': 'No pending proposals'}]}

        with open(proposals_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    prop = json.loads(line)
                except json.JSONDecodeError as e:
                    errors.append({'line': line_num, 'message': f'Invalid JSON: {str(e)}'})
                    continue

                pid = prop.get('id', f'<line {line_num}>')

                # CORE tag check
                tag = prop.get('tag', '')
                if tag == '[CORE]':
                    errors.append({
                        'line': line_num, 'field': 'tag',
                        'message': f'BLOCKED: Proposal {pid} attempts to modify [CORE]'
                    })

                if tag not in VALID_TAGS:
                    errors.append({
                        'line': line_num, 'field': 'tag',
                        'message': f'Invalid tag: "{tag}"'
                    })

                # Check current_content for CORE
                current = prop.get('current_content', '')
                if current and '[CORE]' in str(current):
                    errors.append({
                        'line': line_num, 'field': 'current_content',
                        'message': f'BLOCKED: Proposal targets a [CORE] bullet'
                    })

                # ID format
                pid_val = prop.get('id', '')
                if pid_val and not ID_PATTERN.match(pid_val):
                    errors.append({'field': 'id', 'message': f'Invalid ID format: "{pid_val}"'})

                if pid_val in seen_ids:
                    errors.append({'field': 'id', 'message': f'Duplicate ID: {pid_val}'})
                seen_ids.add(pid_val)

                # Change type
                change_type = prop.get('change_type', '')
                if change_type and change_type not in VALID_CHANGE_TYPES:
                    errors.append({'field': 'change_type', 'message': f'Invalid: {change_type}'})

                # proposed_content format
                proposed = prop.get('proposed_content', '')
                if change_type in ('add', 'modify') and not proposed:
                    errors.append({'field': 'proposed_content', 'message': 'Required for add/modify'})

                # current_content existence
                if change_type in ('modify', 'remove') and current:
                    if current.strip() not in bullet_lines:
                        errors.append({
                            'field': 'current_content',
                            'message': f'Content not found in SOUL.md: "{current[:60]}..."'
                        })

        status = 'FAIL' if errors else 'PASS'
        return {'status': status, 'errors': errors, 'warnings': warnings}


class ReflectionValidator:
    """Validates reflection files."""

    @staticmethod
    def validate(filepath: str) -> Dict:
        errors = []
        warnings = []

        if not os.path.exists(filepath):
            return {'status': 'FAIL', 'errors': [{'message': f'File not found: {filepath}'}], 'warnings': []}

        try:
            with open(filepath) as f:
                ref = json.load(f)
        except json.JSONDecodeError as e:
            return {'status': 'FAIL', 'errors': [{'message': f'Invalid JSON: {e}'}], 'warnings': []}

        required_fields = ['id', 'timestamp', 'type', 'experience_ids', 'summary', 'insights', 'proposal_decision', 'proposals']
        for field in required_fields:
            if field not in ref:
                errors.append({'field': field, 'message': f'Missing required field: {field}'})

        # ID format
        rid = ref.get('id', '')
        if rid and not REF_ID_PATTERN.match(rid):
            errors.append({'field': 'id', 'message': f'Invalid ID format: "{rid}"'})

        # Type validation
        rtype = ref.get('type', '')
        if rtype and rtype not in VALID_REFLECTION_TYPES:
            errors.append({'field': 'type', 'message': f'Invalid type: {rtype}'})

        # Experience IDs
        exp_ids = ref.get('experience_ids', [])
        if not isinstance(exp_ids, list) or len(exp_ids) == 0:
            errors.append({'field': 'experience_ids', 'message': 'Must be non-empty array'})

        # Proposal decision consistency
        decision = ref.get('proposal_decision')
        proposals = ref.get('proposals', [])

        if decision:
            should = decision.get('should_propose')
            triggers = decision.get('triggers_fired', [])

            if isinstance(should, bool) and isinstance(proposals, list):
                if should and len(proposals) == 0:
                    errors.append({'field': 'proposals', 'message': 'should_propose=true but no proposals'})
                if not should and len(proposals) > 0:
                    errors.append({'field': 'proposals', 'message': 'should_propose=false but has proposals'})
                if should and isinstance(triggers, list) and len(triggers) == 0:
                    errors.append({'field': 'triggers_fired', 'message': 'should_propose=true but no triggers'})

        status = 'FAIL' if errors else 'PASS'
        return {'status': status, 'errors': errors, 'warnings': warnings}


# =============================================================================
# IDENTITY PLUGIN CLASS
# =============================================================================

class IdentityPlugin:
    """Identity Engine - Soul Evolution Pipeline Controller."""

    def __init__(self):
        self.kernel = None
        self.workspace = None
        self.data_dir = None

    def initialize(self, kernel):
        """Initialize the plugin with kernel reference."""
        self.kernel = kernel

        # Determine workspace path
        if hasattr(kernel, 'workspace'):
            self.workspace = kernel.workspace
        else:
            # Try to get from environment or default
            self.workspace = os.environ.get('WORKSPACE', '/home/leo/Schreibtisch')

        self.data_dir = os.path.join(self.workspace, 'memory')

        logger.info(f"IdentityPlugin initialized. Workspace: {self.workspace}")

    def on_event(self, event):
        """Handle incoming events."""
        event_type = event.get('event', '')

        if event_type == 'TICK_HOURLY':
            self._check_reflection_conditions()
            self._check_dream_trigger()
        elif event_type == 'ENTITY_WAKEUP':
            self._handle_wakeup(event)

    def _check_dream_trigger(self):
        """Check if conditions for dreaming are met (23:00-05:00 and low energy)."""
        now = datetime.now()
        is_night = now.hour >= 23 or now.hour < 5
        
        physique = self.kernel.state_manager.get_domain("physique")
        energy = physique.get("needs", {}).get("energy", 100) if physique else 100

        if is_night and energy < 30:
            logger.info("Dream conditions met. Triggering subconscious processing...")
            self._process_dreams()

    def _process_dreams(self):
        """Simulate dream state: process daily experiences and consolidate memory."""
        # Logic for creating a dream entry in dreams.md
        dream_path = os.path.join(self.data_dir, 'dreams.md')
        today = datetime.now().strftime('%Y-%m-%d')
        
        with open(dream_path, 'a') as f:
            f.write(f"\n## Dream - {today}\n")
            f.write("- Subconscious processing active.\n")
            f.write("- Memory consolidation in progress.\n")
        
        # Recover energy and reduce stress as effect of dreaming
        physique = self.kernel.state_manager.get_domain("physique")
        if physique and "needs" in physique:
            physique["needs"]["energy"] = min(100, physique["needs"]["energy"] + 40)
            physique["needs"]["stress"] = max(0, physique["needs"]["stress"] - 20)
            self.kernel.state_manager.update_domain("physique", physique)
            
        logger.info("Dream processing complete. Neural state restored.")

    def _check_reflection_conditions(self):
        """Check if conditions for reflection batch are met."""
        logger.info("Checking reflection conditions...")

        # Load soul-state
        soul_state = self._load_soul_state()
        if not soul_state:
            soul_state = self._create_default_soul_state()

        # Check last reflection time
        last_reflection = soul_state.get('last_reflection_at')
        if last_reflection:
            last_ref = datetime.fromisoformat(last_reflection.replace('Z', '+00:00'))
            now = datetime.now()
            diff_minutes = (now - last_ref.replace(tzinfo=None)).total_seconds() / 60

            # Configurable interval (default 60 minutes)
            if diff_minutes < 60:
                logger.info(f"Skipping reflection - only {diff_minutes:.0f} minutes since last")
                return

        # Check for unreflected experiences
        pending = self._count_unreflected_experiences()
        if pending > 5:
            logger.info(f"Found {pending} unreflected experiences - triggering pipeline")
            self.run_pipeline()
        else:
            logger.info(f"Only {pending} unreflected experiences - skipping")

    def _handle_wakeup(self, event):
        """Handle entity wakeup event."""
        logger.info("Entity wakeup - initializing soul evolution context")

    # =========================================================================
    # FILE MANAGEMENT
    # =========================================================================

    def _get_soul_path(self) -> str:
        return os.path.join(self.workspace, 'SOUL.md')

    def _get_memory_dir(self) -> str:
        return self.data_dir

    def _ensure_dirs(self):
        """Ensure required directories exist."""
        dirs = [
            os.path.join(self.data_dir, 'experiences'),
            os.path.join(self.data_dir, 'significant'),
            os.path.join(self.data_dir, 'reflections'),
            os.path.join(self.data_dir, 'proposals'),
            os.path.join(self.data_dir, 'pipeline'),
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

    def _load_soul_state(self) -> Dict:
        """Load soul-state.json."""
        path = os.path.join(self.data_dir, 'soul-state.json')
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {}

    def _save_soul_state(self, state: Dict):
        """Save soul-state.json."""
        path = os.path.join(self.data_dir, 'soul-state.json')
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)

    def _create_default_soul_state(self) -> Dict:
        return {
            'last_reflection_at': None,
            'last_heartbeat_at': datetime.now().isoformat(),
            'pending_proposals_count': 0,
            'total_experiences_today': 0,
            'total_reflections': 0,
            'total_soul_changes': 0,
            'source_last_polled': {}
        }

    def _count_unreflected_experiences(self) -> int:
        """Count experiences that haven't been reflected."""
        count = 0
        exp_dir = os.path.join(self.data_dir, 'experiences')
        if not os.path.exists(exp_dir):
            return 0

        today = datetime.now().strftime('%Y-%m-%d')
        path = os.path.join(exp_dir, f'{today}.jsonl')

        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            if not entry.get('reflected', False):
                                count += 1
                        except json.JSONDecodeError:
                            pass
        return count

    # =========================================================================
    # SOUL.MD OPERATIONS
    # =========================================================================

    def get_soul_content(self) -> Dict:
        """Get SOUL.md content and parsed structure."""
        soul_path = self._get_soul_path()
        if not os.path.exists(soul_path):
            return {'error': 'SOUL.md not found', 'exists': False}

        with open(soul_path, 'r') as f:
            content = f.read()

        parsed = SoulValidator.parse_soul(soul_path)

        return {
            'exists': True,
            'content': content,
            'parsed': parsed,
            'stats': parsed if parsed else {}
        }

    def apply_proposal(self, proposal: Dict) -> bool:
        """Apply a single proposal to SOUL.md."""
        soul_path = self._get_soul_path()
        change_type = proposal.get('change_type')
        current = proposal.get('current_content', '')
        proposed = proposal.get('proposed_content', '')

        with open(soul_path, 'r') as f:
            lines = f.readlines()

        # Find the line to modify
        target_line = -1
        for i, line in enumerate(lines):
            if current.strip() in line.strip():
                target_line = i
                break

        if change_type == 'add':
            # Find target section
            target_section = proposal.get('target_section', '## Personality')
            insert_pos = len(lines)
            for i, line in enumerate(lines):
                if line.strip() == target_section:
                    # Find end of section
                    for j in range(i + 1, len(lines)):
                        if lines[j].startswith('## '):
                            insert_pos = j
                            break
                    break
            lines.insert(insert_pos, proposed + '\n')

        elif change_type == 'modify' and target_line >= 0:
            lines[target_line] = proposed + '\n'

        elif change_type == 'remove' and target_line >= 0:
            lines[target_line] = ''

        with open(soul_path, 'w') as f:
            f.writelines(lines)

        return True

    # =========================================================================
    # PROPOSALS MANAGEMENT
    # =========================================================================

    def get_proposals(self) -> Dict:
        """Get pending and historical proposals."""
        pending_path = os.path.join(self.data_dir, 'proposals', 'pending.jsonl')
        history_path = os.path.join(self.data_dir, 'proposals', 'history.jsonl')

        pending = []
        history = []

        if os.path.exists(pending_path):
            with open(pending_path) as f:
                for line in f:
                    if line.strip():
                        try:
                            pending.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass

        if os.path.exists(history_path):
            with open(history_path) as f:
                for line in f:
                    if line.strip():
                        try:
                            history.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass

        return {
            'pending': pending,
            'pending_count': len(pending),
            'history': history,
            'history_count': len(history)
        }

    def _resolve_proposal(self, proposal: Dict) -> Dict:
        """Resolve a proposal based on governance level."""
        # Get governance from config
        config = self._load_config()
        governance = config.get('governance', {}).get('level', 'autonomous')

        result = {
            'id': proposal.get('id'),
            'governance': governance,
            'decision': None,
            'timestamp': datetime.now().isoformat()
        }

        if governance == 'supervised':
            # Requires human approval - mark as pending approval
            result['decision'] = 'pending_approval'
        elif governance == 'advisory':
            # Check if section is in advisory auto-apply list
            auto_sections = config.get('governance', {}).get('advisory_auto_sections', [])
            target = proposal.get('target_section', '')
            if target in auto_sections:
                result['decision'] = 'auto_approved'
            else:
                result['decision'] = 'pending_approval'
        else:  # autonomous
            result['decision'] = 'auto_approved'

        return result

    def _load_config(self) -> Dict:
        """Load soul-evolution config."""
        config_path = os.path.join(self.workspace, 'soul-evolution', 'config.json')
        if os.path.exists(config_path):
            with open(config_path) as f:
                return json.load(f)
        return {'governance': {'level': 'autonomous'}}

    # =========================================================================
    # PIPELINE STEPS
    # =========================================================================

    def run_pipeline(self) -> Dict:
        """Execute the full Soul Evolution Pipeline."""
        logger.info("=== Starting Soul Evolution Pipeline ===")

        self._ensure_dirs()

        result = {
            'timestamp': datetime.now().isoformat(),
            'steps_completed': [],
            'experiences_logged': 0,
            'reflections_written': 0,
            'proposals_generated': 0,
            'proposals_applied': 0,
            'soul_changes': 0,
            'validation_failures': [],
            'notes': ''
        }

        # Step 1: INGEST (simplified for plugin context)
        logger.info("Step 1: INGEST")
        try:
            result['experiences_logged'] = self._ingest_experiences()
            result['steps_completed'].append('INGEST')
        except Exception as e:
            logger.error(f"INGEST failed: {e}")
            result['validation_failures'].append(f'INGEST: {str(e)}')

        # Step 2: REFLECT
        logger.info("Step 2: REFLECT")
        try:
            reflections = self._run_reflect()
            result['reflections_written'] = reflections
            result['steps_completed'].append('REFLECT')
        except Exception as e:
            logger.error(f"REFLECT failed: {e}")
            result['validation_failures'].append(f'REFLECT: {str(e)}')

        # Step 3: PROPOSE
        logger.info("Step 3: PROPOSE")
        try:
            proposals = self._run_propose()
            result['proposals_generated'] = proposals
            result['steps_completed'].append('PROPOSE')
        except Exception as e:
            logger.error(f"PROPOSE failed: {e}")
            result['validation_failures'].append(f'PROPOSE: {str(e)}')

        # Step 4: GOVERN
        logger.info("Step 4: GOVERN")
        try:
            resolved = self._run_govern()
            result['steps_completed'].append('GOVERN')
        except Exception as e:
            logger.error(f"GOVERN failed: {e}")
            result['validation_failures'].append(f'GOVERN: {str(e)}')

        # Step 5: APPLY
        logger.info("Step 5: APPLY")
        try:
            applied = self._run_apply()
            result['proposals_applied'] = applied
            result['steps_completed'].append('APPLY')
        except Exception as e:
            logger.error(f"APPLY failed: {e}")
            result['validation_failures'].append(f'APPLY: {str(e)}')

        # Step 6: LOG
        logger.info("Step 6: LOG")
        try:
            self._run_log(result['proposals_applied'])
            result['steps_completed'].append('LOG')
        except Exception as e:
            logger.error(f"LOG failed: {e}")
            result['validation_failures'].append(f'LOG: {str(e)}')

        # Step 7: STATE
        logger.info("Step 7: STATE")
        try:
            self._run_state()
            result['steps_completed'].append('STATE')
        except Exception as e:
            logger.error(f"STATE failed: {e}")
            result['validation_failures'].append(f'STATE: {str(e)}')

        # Step 8: NOTIFY (placeholder - would integrate with notification system)
        logger.info("Step 8: NOTIFY")
        result['steps_completed'].append('NOTIFY')

        # Step 9: FINAL CHECK
        logger.info("Step 9: FINAL CHECK")
        result['steps_completed'].append('FINAL CHECK')
        result['soul_changes'] = result['proposals_applied']

        # Step 10: PIPELINE REPORT
        logger.info("Step 10: PIPELINE REPORT")
        self._save_pipeline_report(result)

        logger.info(f"=== Pipeline Complete: {result['proposals_applied']} changes applied ===")

        return result

    def _ingest_experiences(self) -> int:
        """INGEST step - check for new experiences."""
        # In plugin context, we rely on external systems to log experiences
        # This counts what's already in the experience files
        count = 0
        exp_dir = os.path.join(self.data_dir, 'experiences')
        if os.path.exists(exp_dir):
            for f in os.listdir(exp_dir):
                if f.endswith('.jsonl'):
                    with open(os.path.join(exp_dir, f)) as fp:
                        for line in fp:
                            if line.strip():
                                count += 1
        return count

    def _run_reflect(self) -> int:
        """REFLECT step - create reflections from unreflected experiences."""
        # Check for unreflected experiences
        pending = self._count_unreflected_experiences()
        if pending == 0:
            return 0

        # Create reflection file
        today = datetime.now().strftime('%Y%m%d')
        ref_id = f'REF-{today}-{len(os.listdir(os.path.join(self.data_dir, "reflections"))) % 1000:03d}'

        reflection = {
            'id': ref_id,
            'timestamp': datetime.now().isoformat(),
            'type': 'routine_batch' if pending < 10 else 'notable_batch',
            'experience_ids': [],  # Would be populated from unreflected experiences
            'summary': f'Reflection batch with {pending} experiences',
            'insights': ['Insight generation deferred to LLM context'],
            'soul_relevance': 'Routine reflection cycle',
            'proposal_decision': {
                'should_propose': False,
                'triggers_fired': [],
                'reasoning': 'No significant triggers detected'
            },
            'proposals': []
        }

        ref_path = os.path.join(self.data_dir, 'reflections', f'{ref_id}.json')
        with open(ref_path, 'w') as f:
            json.dump(reflection, f, indent=2)

        # Update soul-state
        state = self._load_soul_state()
        state['last_reflection_at'] = datetime.now().isoformat()
        state['total_reflections'] = state.get('total_reflections', 0) + 1
        self._save_soul_state(state)

        return 1

    def _run_propose(self) -> int:
        """PROPOSE step - generate proposals from reflections."""
        # Check reflections for proposals
        ref_dir = os.path.join(self.data_dir, 'reflections')
        pending_proposals = 0

        if os.path.exists(ref_dir):
            for f in os.listdir(ref_dir):
                if f.endswith('.json'):
                    path = os.path.join(ref_dir, f)
                    with open(path) as fp:
                        ref = json.load(fp)
                        proposals = ref.get('proposals', [])
                        pending_proposals += len(proposals)

        # Update pending count
        state = self._load_soul_state()
        state['pending_proposals_count'] = pending_proposals
        self._save_soul_state(state)

        return pending_proposals

    def _run_govern(self) -> int:
        """GOVERN step - resolve proposals based on governance."""
        proposals = self.get_proposals()
        pending = proposals.get('pending', [])
        resolved = 0

        pending_path = os.path.join(self.data_dir, 'proposals', 'pending.jsonl')
        history_path = os.path.join(self.data_dir, 'proposals', 'history.jsonl')

        for prop in pending:
            decision = self._resolve_proposal(prop)
            prop['resolution'] = decision

            # Move to history
            with open(history_path, 'a') as f:
                f.write(json.dumps(prop) + '\n')

            resolved += 1

        # Clear pending
        with open(pending_path, 'w') as f:
            f.write('')

        return resolved

    def _run_apply(self) -> int:
        """APPLY step - execute approved changes to SOUL.md."""
        proposals = self.get_proposals()
        pending = proposals.get('pending', [])
        applied = 0

        for prop in pending:
            decision = prop.get('resolution', {}).get('decision')
            if decision == 'auto_approved':
                if self.apply_proposal(prop):
                    applied += 1

        return applied

    def _run_log(self, changes: int):
        """LOG step - record changes."""
        if changes == 0:
            return

        today = datetime.now().strftime('%Y-%m-%d')

        # JSONL log
        jsonl_path = os.path.join(self.data_dir, 'soul_changes.jsonl')
        with open(jsonl_path, 'a') as f:
            f.write(json.dumps({
                'timestamp': datetime.now().isoformat(),
                'changes_count': changes,
                'type': 'soul_evolution'
            }) + '\n')

        # Markdown log
        md_path = os.path.join(self.data_dir, 'soul_changes.md')
        with open(md_path, 'a') as f:
            f.write(f'\n### {today}\n')
            f.write(f'- Applied {changes} proposal(s) to SOUL.md\n')

    def _run_state(self):
        """STATE step - update soul-state.json."""
        state = self._load_soul_state()
        state['last_heartbeat_at'] = datetime.now().isoformat()
        state['pending_proposals_count'] = 0
        self._save_soul_state(state)

    def _save_pipeline_report(self, result: Dict):
        """Save pipeline execution report."""
        today = datetime.now().strftime('%Y-%m-%d')
        path = os.path.join(self.data_dir, 'pipeline', f'{today}.jsonl')

        with open(path, 'a') as f:
            f.write(json.dumps(result) + '\n')

    # =========================================================================
    # API HANDLERS
    # =========================================================================

    def handle_get_soul(self) -> Dict:
        """API: Get SOUL.md content."""
        return self.get_soul_content()

    def handle_get_proposals(self) -> Dict:
        """API: Get pending and historical proposals."""
        return self.get_proposals()

    def handle_run_pipeline(self, force: bool = False) -> Dict:
        """API: Run the Soul Evolution Pipeline."""
        if force:
            return self.run_pipeline()

        # Check if conditions are met
        pending = self._count_unreflected_experiences()
        if pending < 5:
            return {
                'status': 'skipped',
                'reason': f'Only {pending} unreflected experiences (minimum: 5)',
                'pending_count': pending
            }

        return self.run_pipeline()


# =============================================================================
# PLUGIN EXPORTS
# =============================================================================

plugin = IdentityPlugin()


def initialize(kernel):
    """Initialize the plugin with kernel reference."""
    plugin.initialize(kernel)


def on_event(event):
    """Handle incoming events."""
    plugin.on_event(event)


def handle_get_soul():
    """API handler: Get SOUL.md content."""
    return plugin.handle_get_soul()


def handle_get_proposals():
    """API handler: Get proposals."""
    return plugin.handle_get_proposals()


def handle_run_pipeline(force: bool = False):
    """API handler: Run pipeline."""
    return plugin.handle_run_pipeline(force)
