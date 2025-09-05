# Guide: Adding a New Hardware Feature (Potentiometer-Controlled Spotlight Dimming)

## Overview
This guide walks you through integrating a potentiometer for spotlight dimming into your modular, event-driven Python system. The approach ensures the new sensor and its state are accessible to all components, and that events are published and consumed in a scalable way.

---

## 1. Define the Data Model
- **Why:** Centralizes all relevant state in one place, making it accessible to all components.
- **How:** Update your `StateManager` (or similar) to include fields for potentiometer value and spotlight level.

```python
# Example addition to StateManager
self.potentiometer_value = 0
self.spotlight_level = 0
```

---

## 2. Create Event Classes
- **Why:** Events are the backbone of your pub-sub system. They allow components to react to changes.
- **How:** In your `events.py`, define new event classes for potentiometer changes and spotlight level changes.

```python
class PotentiometerChangedEvent(Event):
    """Triggered when potentiometer value changes"""
    pass

class SpotlightLevelChangedEvent(Event):
    """Triggered when spotlight level changes"""
    pass
```

---

## 3. Implement the Sensor Reader
- **Why:** Encapsulates hardware access and publishes events when values change or thresholds are crossed.
- **How:** Add a new class (e.g., `PotentiometerReader`) that reads the potentiometer, updates state, and publishes events.
- Use configurable thresholds from your `config.py` for event triggering.

---

## 4. Update the StateManager
- **Why:** Ensures all components can access the latest potentiometer and spotlight values.
- **How:** Add methods to update and retrieve these values. Subscribe to the new events to update state.

---

## 5. Publish Events on Thresholds
- **Why:** Allows other components to react to significant changes (e.g., dimming below a certain level).
- **How:** In your sensor reader, compare the value to thresholds and publish events when crossed.

---

## 6. Subscribe and React in Other Components
- **Why:** Enables features like logging, UI updates, or automated actions based on light level.
- **How:** In any component, subscribe to the new events and implement handlers.

---

## 7. Add Configuration Options
- **Why:** Makes thresholds and behavior easily adjustable.
- **How:** Add new fields to `config.py` for potentiometer thresholds, spotlight min/max, etc.

---

## 8. Test and Document
- **Why:** Ensures reliability and helps others understand the feature.
- **How:** Write unit/integration tests and update documentation.

---

## Example Workflow
1. **Update `config.py`**: Add `potentiometer_thresholds`, `spotlight_min`, `spotlight_max`.
2. **Add events to `events.py`**: `PotentiometerChangedEvent`, `SpotlightLevelChangedEvent`.
3. **Implement `PotentiometerReader`**: Read hardware, publish events.
4. **Update `StateManager`**: Store and update values, subscribe to events.
5. **Subscribe in other components**: E.g., logging, UI, automation.
6. **Test and document**: Ensure everything works and is clear.

---

## Why This Process?
- **Modularity:** Each component has a clear responsibility.
- **Scalability:** New features/events can be added without breaking existing code.
- **Configurability:** Behavior can be tuned via config, not code changes.
- **Observability:** State and events are visible to all components.

---

Feel free to share this guide with your team! It’s designed to help you and others add new hardware features in a maintainable, scalable way.
