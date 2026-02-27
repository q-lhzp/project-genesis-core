"""
Hobby Engine Plugin - Interests & Research Simulation
Manages user interests, hobbies, and idle research insights.
"""

import json
import logging
import random
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='[HOBBY] %(message)s')
logger = logging.getLogger("hobby")

# =============================================================================
# CONSTANTS & RESEARCH TOPICS
# =============================================================================

RESEARCH_TOPICS = [
    "quantum computing", "neural networks", "blockchain", "biotechnology",
    "space exploration", "renewable energy", "robotics", "AI ethics",
    "virtual reality", "augmented reality", "cryptography", "IoT",
    "edge computing", "5G networks", "quantum cryptography", "genome editing",
    "stem cell research", "neurotechnology", "brain-computer interfaces",
    "nanotechnology", "advanced materials", "fusion energy", "climate modeling",
    "cognitive science", "behavioral economics", "game theory", "complex systems",
    "systems biology", "synthetic biology", "precision medicine", "immunotherapy"
]

RESEARCH_INSIGHT_TEMPLATES = [
    "Interesting development in {topic}: recent breakthroughs suggest new applications",
    "Research update on {topic}: new papers indicate promising directions",
    "Note: {topic} is evolving rapidly - consider exploring depth over breadth",
    "Insight: {topic} intersects with your existing interests in unexpected ways",
    "Quick update: {topic} has seen {percent}% growth in research activity",
    "FYI: A new framework for {topic} was published this week",
    "Thought: How might {topic} influence your long-term goals?",
    "Bookmark: {topic} - potential for cross-disciplinary collaboration"
]

DEFAULT_INTERESTS = {
    "interests": [],
    "hobbies": [],
    "research_insights": [],
    "last_research_at": None,
    "curiosity_score": 50
}

# =============================================================================
# PLUGIN CLASS
# =============================================================================

class HobbyPlugin:
    """Hobby Engine - Manages interests, hobbies, and research insights."""

    def __init__(self):
        self.kernel = None
        self.workspace = None

    def initialize(self, kernel):
        """Initialize the plugin with kernel reference."""
        self.kernel = kernel

        # Determine workspace path
        if hasattr(kernel, 'workspace'):
            self.workspace = kernel.workspace
        else:
            self.workspace = getattr(kernel, 'workspace', '/home/leo/Schreibtisch')

        logger.info(f"HobbyPlugin initialized. Workspace: {self.workspace}")

        # Initialize interests domain if not exists
        self._ensure_interests_domain()

    def _ensure_interests_domain(self):
        """Ensure the interests state domain exists."""
        interests = self.kernel.state_manager.get_domain("interests")
        if not interests:
            self.kernel.state_manager.update_domain("interests", DEFAULT_INTERESTS.copy())
            logger.info("Created default interests domain")

    def on_event(self, event):
        """Handle incoming events."""
        event_type = event.get("event", "")

        if event_type == "TICK_HOURLY":
            self._handle_hourly_tick()
        elif event_type == "INTEREST_UPDATED":
            self._handle_interest_updated(event)
        elif event_type == "RESEARCH_TRIGGER":
            self._trigger_research(event)

    def _handle_hourly_tick(self):
        """Handle hourly tick - occasionally log research insights."""
        # 30% chance to generate a research insight per hour
        if random.random() < 0.30:
            self._generate_research_insight()
        else:
            logger.debug("No research insight generated this hour")

    def _generate_research_insight(self):
        """Generate and log a research insight."""
        interests = self.kernel.state_manager.get_domain("interests")
        if not interests:
            return

        # Select random topic
        topic = random.choice(RESEARCH_TOPICS)

        # Select random template
        template = random.choice(RESEARCH_INSIGHT_TEMPLATES)

        # Generate percentage for templates that need it
        percent = random.randint(10, 100)
        insight_text = template.format(topic=topic, percent=percent)

        # Create insight object
        insight = {
            "id": f"INS-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "text": insight_text,
            "category": "research"
        }

        # Store insight
        insights = interests.get("research_insights", [])
        insights.append(insight)

        # Keep only last 50 insights
        if len(insights) > 50:
            insights = insights[-50:]

        interests["research_insights"] = insights
        interests["last_research_at"] = datetime.now().isoformat()

        self.kernel.state_manager.update_domain("interests", interests)

        # Publish event for presence feed
        if hasattr(self.kernel, 'publish_event'):
            self.kernel.publish_event({
                "event": "EVENT_RESEARCH_COMPLETE",
                "source": "hobby-engine",
                "data": insight
            })

        logger.info(f"Research insight generated: {topic}")

    def _handle_interest_updated(self, event):
        """Handle interest update event."""
        logger.debug(f"Interest updated: {event.get('data')}")

    def _trigger_research(self, event):
        """Manually trigger research insight generation."""
        self._generate_research_insight()

    # =========================================================================
    # API HANDLERS
    # =========================================================================

    def handle_get_interests(self) -> Dict:
        """API: Get all interests and hobbies."""
        interests = self.kernel.state_manager.get_domain("interests")
        if not interests:
            interests = DEFAULT_INTERESTS.copy()
            self.kernel.state_manager.update_domain("interests", interests)

        return {
            "status": "success",
            "interests": interests.get("interests", []),
            "hobbies": interests.get("hobbies", []),
            "research_insights": interests.get("research_insights", []),
            "curiosity_score": interests.get("curiosity_score", 50),
            "last_research_at": interests.get("last_research_at")
        }

    def handle_add_interest(self, data: Dict = None) -> Dict:
        """API: Add a new interest or hobby.

        Args:
            data: Dict with 'name', 'type' (interest/hobby), 'category', 'intensity'

        Returns:
            Status and updated interests list
        """
        if not data:
            return {"status": "error", "message": "No data provided"}

        name = data.get("name", "").strip()
        interest_type = data.get("type", "interest").lower()
        category = data.get("category", "general")
        intensity = data.get("intensity", 5)

        if not name:
            return {"status": "error", "message": "Interest name is required"}

        # Validate type
        if interest_type not in ["interest", "hobby"]:
            return {"status": "error", "message": "Type must be 'interest' or 'hobby'"}

        # Load current interests
        interests = self.kernel.state_manager.get_domain("interests")
        if not interests:
            interests = DEFAULT_INTERESTS.copy()

        # Check for duplicates
        target_list = interests.get(interest_type + "s", [])
        existing_names = [i.get("name", "").lower() for i in target_list]

        if name.lower() in existing_names:
            return {"status": "error", "message": f"'{name}' already exists as {interest_type}"}

        # Create new interest object
        new_interest = {
            "id": f"{interest_type.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": name,
            "category": category,
            "intensity": min(10, max(1, intensity)),
            "added_at": datetime.now().isoformat(),
            "last_engaged": datetime.now().isoformat()
        }

        # Add to appropriate list
        target_list.append(new_interest)
        interests[interest_type + "s"] = target_list

        # Update curiosity score based on new interest
        current_score = interests.get("curiosity_score", 50)
        interests["curiosity_score"] = min(100, current_score + 2)

        # Save
        self.kernel.state_manager.update_domain("interests", interests)

        # Publish event
        if hasattr(self.kernel, 'publish_event'):
            self.kernel.publish_event({
                "event": "EVENT_NEW_INTEREST_FOUND",
                "source": "hobby-engine",
                "data": new_interest
            })

        logger.info(f"Added new {interest_type}: {name}")

        return {
            "status": "success",
            "message": f"Added {interest_type}: {name}",
            "interest": new_interest,
            "curiosity_score": interests.get("curiosity_score")
        }

    def handle_remove_interest(self, data: Dict = None) -> Dict:
        """API: Remove an interest or hobby.

        Args:
            data: Dict with 'name' or 'id', and 'type' (interest/hobby)

        Returns:
            Status and updated interests list
        """
        if not data:
            return {"status": "error", "message": "No data provided"}

        name = data.get("name", "").strip()
        interest_id = data.get("id", "").strip()
        interest_type = data.get("type", "interest").lower()

        if not name and not interest_id:
            return {"status": "error", "message": "Name or ID is required"}

        if interest_type not in ["interest", "hobby"]:
            return {"status": "error", "message": "Type must be 'interest' or 'hobby'"}

        # Load current interests
        interests = self.kernel.state_manager.get_domain("interests")
        if not interests:
            return {"status": "error", "message": "No interests found"}

        # Find and remove
        target_list = interests.get(interest_type + "s", [])
        original_length = len(target_list)

        if interest_id:
            target_list = [i for i in target_list if i.get("id") != interest_id]
        else:
            target_list = [i for i in target_list if i.get("name", "").lower() != name.lower()]

        if len(target_list) == original_length:
            return {"status": "error", "message": f"{interest_type.capitalize()} not found"}

        interests[interest_type + "s"] = target_list

        # Decrease curiosity score
        current_score = interests.get("curiosity_score", 50)
        interests["curiosity_score"] = max(0, current_score - 1)

        self.kernel.state_manager.update_domain("interests", interests)

        return {
            "status": "success",
            "message": f"Removed {interest_type}: {name or interest_id}"
        }

    def handle_update_curiosity(self, score: int = None) -> Dict:
        """API: Update curiosity score.

        Args:
            score: New curiosity score (0-100)

        Returns:
            Updated curiosity score
        """
        if score is None:
            return {"status": "error", "message": "Score is required"}

        score = max(0, min(100, score))

        interests = self.kernel.state_manager.get_domain("interests")
        if not interests:
            interests = DEFAULT_INTERESTS.copy()

        interests["curiosity_score"] = score
        self.kernel.state_manager.update_domain("interests", interests)

        return {
            "status": "success",
            "curiosity_score": score
        }

    def handle_get_research_insights(self, limit: int = 10) -> Dict:
        """API: Get recent research insights.

        Args:
            limit: Maximum number of insights to return

        Returns:
            List of research insights
        """
        interests = self.kernel.state_manager.get_domain("interests")
        if not interests:
            return {"status": "success", "insights": []}

        insights = interests.get("research_insights", [])
        return {
            "status": "success",
            "insights": insights[-limit:] if limit > 0 else insights,
            "count": len(insights)
        }

    def handle_trigger_insight(self) -> Dict:
        """API: Manually trigger a research insight."""
        self._generate_research_insight()

        interests = self.kernel.state_manager.get_domain("interests")
        latest = interests.get("research_insights", [])[-1] if interests.get("research_insights") else None

        return {
            "status": "success",
            "insight": latest,
            "message": "Research insight generated"
        }


# =============================================================================
# PLUGIN EXPORTS
# =============================================================================

plugin = HobbyPlugin()


def initialize(kernel):
    """Initialize the plugin with kernel reference."""
    plugin.initialize(kernel)


def on_event(event):
    """Handle incoming events."""
    plugin.on_event(event)


def handle_get_interests():
    """API handler: Get all interests and hobbies."""
    return plugin.handle_get_interests()


def handle_add_interest(data: Dict = None):
    """API handler: Add a new interest or hobby."""
    return plugin.handle_add_interest(data)


def handle_remove_interest(data: Dict = None):
    """API handler: Remove an interest or hobby."""
    return plugin.handle_remove_interest(data)


def handle_update_curiosity(score: int = None):
    """API handler: Update curiosity score."""
    return plugin.handle_update_curiosity(score)


def handle_get_research_insights(limit: int = 10):
    """API handler: Get research insights."""
    return plugin.handle_get_research_insights(limit)


def handle_trigger_insight():
    """API handler: Manually trigger research insight."""
    return plugin.handle_trigger_insight()
