<!--

// 2025-08-29
// claude.ai, using sonnet 4 and expanded thinking: https://claude.ai/chat/0e23f63c-533a-4231-8bb8-7b495b477977
// working on my messing around with asyncio code with the prompt:
### claude.ai
#### prompt  
While I have lots of ideas on how to expand it further, I think it's best to first take a step back and work on what is already there. 

I would like to use the new insights and developed methods in other projects, or to make them accessible to coworkers/friends. 

Goal One: would be to develop some clear documentation as to how it works, why certain things work. You have already begun this part, but it would be nice to have a refined and ordered explanation (for example, the various coroutines have been created as I came up with them, so there's not really a process from top to bottom, which shows how new ideas and patterns building on earlier ones are added). I think either a well commented python file, a markdown, or even a jupyter notebook would be a great format (though I'm unsure how well jupyter actually handles asyncio. Maybe you have more experience). 

Goal Two: would be to present the offer of NOT having to read the documentation and understand asyncio, but to simply provide an easy to use interface or adoption guide on how to add the eventbus to one's own synchronous script or how to make the eventbus activate one's synchronous functions/methods, or interact with the State class. 

If you can do both in one go, I would love that (take your time, I'm in no rush. I'd prefer a well thought-through quality work, over quick results), but for now, I think Goal Two is the focus.


#### thought process  

The user has two goals:

Create clear documentation explaining how the asyncio system works, showing the progression of patterns and how they build on each other
Create an easy-to-use interface for people to integrate the EventBus into their synchronous code without having to understand asyncio

They want me to focus on Goal Two, which is about making this accessible to people who don't want to learn asyncio but want to benefit from the event-driven patterns.
For Goal Two, I need to think about what would make this truly easy for someone with synchronous code:

A wrapper that lets them register synchronous functions as event handlers
A way to publish events from synchronous code
A way to integrate with existing synchronous workflows
Simple examples showing before/after

The key insight is that most people have synchronous functions they want to connect, so I need to create bridges between the async world and the sync world.
I should create an artifact that provides:

A SyncEventBridge class that wraps the EventBus
Decorators for easy function registration
Simple publish methods
Clear examples of how to integrate
Maybe a State integration helper too

Let me focus on creating a really good, easy-to-use interface.


#### response

You're absolutely right to focus on Goal Two first! The best way to make this valuable to others is to remove the asyncio learning curve entirely. Let me create an easy-to-use interface that lets people integrate event-driven patterns into their existing synchronous code without having to understand the async machinery underneath.I've created two artifacts for you:

1. **`EasyEvents` class** - A synchronous interface that completely hides the asyncio complexity
2. **Comprehensive adoption guide** - Shows exactly how to integrate it into existing projects

##### What Makes This Easy to Adopt

**No asyncio knowledge required**: Your coworkers can use decorators like `@events.on('user_login')` and `events.publish('user_login', username)` without understanding async/await.

**Multiple integration patterns**: 
- **Retrofit existing code** - Add events without changing core logic
- **Replace callback hell** - Clean up complex callback chains  
- **Add monitoring** - Background tasks and health checks
- **Create pipelines** - Chain operations with events

**Flexible running modes**:
- `events.run_for(seconds=2)` - Process events for a specific time
- `events.run_forever()` - Traditional main loop  
- `events.run_in_background()` - Non-blocking background processing

##### Key Features I Added

- **Automatic argument unpacking**: Events can pass dicts, lists, or single values and handlers receive them naturally
- **Shared state management**: `shared_state` object for coordination between handlers
- **Periodic tasks**: `@events.every(5.0)` decorator for background monitoring
- **Error isolation**: Handler exceptions don't crash the system
- **Easy testing**: Capture events in tests to verify behavior

The adoption guide shows real before/after examples, so people can see exactly how to apply it to their existing order processors, file handlers, database code, etc.

This approach means someone can start using event-driven patterns in 5 minutes, then gradually learn the deeper concepts as they need them. Would you like me to refine any particular aspect or add specific integration examples for common use cases?

-->

# Event System Adoption Guide

## 🎯 Quick Start - Add Events to Any Python Project

No asyncio knowledge required! This guide shows you how to add event-driven patterns to your existing synchronous code in minutes.

## 📦 Installation

Just copy the `EasyEvents` class into your project, or save it as `sync_event_system.py` and import it.

```python
from sync_event_system import EasyEvents, shared_state
```

## 🚀 Pattern 1: Add Events to Existing Functions

**Before (regular code):**
```python
class OrderProcessor:
    def __init__(self):
        self.orders = []
    
    def process_order(self, order_id, customer, items):
        print(f"Processing order {order_id}")
        self.orders.append({'id': order_id, 'customer': customer, 'items': items})
        print("Order completed")
```

**After (with events):**
```python
events = EasyEvents()

class OrderProcessor:
    def __init__(self):
        self.orders = []
    
    def process_order(self, order_id, customer, items):
        # Trigger event at start
        events.publish('order_started', {
            'order_id': order_id, 
            'customer': customer, 
            'items': items
        })
        
        print(f"Processing order {order_id}")
        self.orders.append({'id': order_id, 'customer': customer, 'items': items})
        
        # Trigger event at completion
        events.publish('order_completed', {
            'order_id': order_id, 
            'customer': customer
        })

# Now other parts of your system can react to orders:
@events.on('order_started')
def send_confirmation_email(order_id, customer, items):
    print(f"📧 Sending confirmation to {customer} for order {order_id}")

@events.on('order_completed') 
def update_inventory(order_id, customer):
    print(f"📦 Updating inventory for order {order_id}")

@events.on('order_completed')
def log_analytics(order_id, customer):
    shared_state.total_orders = getattr(shared_state, 'total_orders', 0) + 1
    print(f"📊 Total orders processed: {shared_state.total_orders}")

# Use it:
processor = OrderProcessor()
processor.process_order("ORD123", "Alice", ["laptop", "mouse"])
events.run_for(seconds=1)  # Let events process
```

## 🔄 Pattern 2: Replace Callback Hell

**Before (callback nightmare):**
```python
def download_file(url, on_progress, on_complete, on_error):
    # ... downloading logic ...
    on_progress(50)
    # ... more logic ...
    on_complete(filepath)

def process_download():
    def progress_cb(percent):
        print(f"Progress: {percent}%")
    
    def complete_cb(filepath):
        print(f"Downloaded to {filepath}")
        validate_file(filepath, error_cb, success_cb)
    
    def error_cb(error):
        print(f"Error: {error}")
    
    def success_cb():
        print("File validated!")
    
    download_file("http://example.com/file.zip", progress_cb, complete_cb, error_cb)
```

**After (clean events):**
```python
events = EasyEvents()

@events.on('download_progress')
def show_progress(percent):
    print(f"Progress: {percent}%")

@events.on('download_complete')
def handle_complete(filepath):
    print(f"Downloaded to {filepath}")
    events.publish('validate_file', filepath)

@events.on('validate_file')
def validate_file(filepath):
    # ... validation logic ...
    events.publish('file_validated', filepath)

@events.on('file_validated')
def celebrate(filepath):
    print("File validated! 🎉")

def download_file(url):
    # ... downloading logic ...
    events.publish('download_progress', 50)
    # ... more logic ... 
    events.publish('download_complete', '/tmp/file.zip')

# Much cleaner!
download_file("http://example.com/file.zip")
events.run_for(seconds=2)
```

## ⏰ Pattern 3: Add Background Monitoring

```python
events = EasyEvents(debug=True)

# Your existing business logic stays unchanged
class DatabaseConnection:
    def __init__(self):
        self.connected = True
        self.query_count = 0
    
    def query(self, sql):
        if not self.connected:
            raise Exception("Not connected!")
        self.query_count += 1
        events.publish('db_query_executed', {'sql': sql, 'count': self.query_count})
        return f"Results for: {sql}"

# Add monitoring without changing existing code
@events.every(3.0)  # Check every 3 seconds
def health_check():
    shared_state.last_health_check = time.time()
    events.publish('system_heartbeat', {'timestamp': shared_state.last_health_check})

@events.on('db_query_executed')
def monitor_db_usage(sql, count):
    if count > 100:
        events.publish('alert', {'type': 'high_db_usage', 'count': count})

@events.on('alert')
def handle_alert(type, **data):
    print(f"🚨 ALERT: {type} - {data}")

@events.on('system_heartbeat')
def log_heartbeat(timestamp):
    print(f"💓 System healthy at {timestamp}")

# Your code works exactly the same, but now has monitoring
db = DatabaseConnection()
result = db.query("SELECT * FROM users")
print(result)

# Run the monitoring in background
stop_monitoring = events.run_in_background()

# Your main program continues...
time.sleep(10)  # Simulate work

stop_monitoring()  # Clean shutdown
```

## 🔗 Pattern 4: Chain Operations with Events

```python
events = EasyEvents()

# Create a processing pipeline using events
@events.on('file_uploaded')
def validate_file(filename, user):
    print(f"✅ Validating {filename}")
    if filename.endswith('.txt'):
        events.publish('file_valid', {'filename': filename, 'user': user})
    else:
        events.publish('file_invalid', {'filename': filename, 'user': user})

@events.on('file_valid')
def process_file(filename, user):
    print(f"⚙️ Processing {filename}")
    # Simulate processing time
    shared_state.processed_files = getattr(shared_state, 'processed_files', 0) + 1
    events.publish('file_processed', {'filename': filename, 'user': user})

@events.on('file_processed')  
def notify_user(filename, user):
    print(f"📤 Notifying {user}: {filename} is ready")

@events.on('file_invalid')
def reject_file(filename, user):
    print(f"❌ Rejected {filename} from {user}")

# Trigger the pipeline
events.publish('file_uploaded', {'filename': 'data.txt', 'user': 'Alice'})
events.publish('file_uploaded', {'filename': 'image.jpg', 'user': 'Bob'})  
events.run_for(seconds=1)

print(f"Files processed: {shared_state.processed_files}")
```

## 🛠️ Pattern 5: Retrofit Legacy Code

Say you have existing code that's hard to test or extend:

```python
# Your existing hard-to-test code
class LegacyReport:
    def generate_report(self, data):
        # Lots of steps that are hard to test individually
        self.validate_data(data)
        processed = self.process_data(data) 
        formatted = self.format_report(processed)
        self.save_report(formatted)
        self.email_report(formatted)
        return formatted
    
    def validate_data(self, data): 
        if not data: raise ValueError("No data")
        
    def process_data(self, data):
        return [x*2 for x in data]
        
    def format_report(self, data):
        return f"Report: {data}"
        
    def save_report(self, report):
        print("💾 Report saved")
        
    def email_report(self, report): 
        print("📧 Report emailed")
```

**Add events without changing the main logic:**

```python
events = EasyEvents()

class EventDrivenReport(LegacyReport):
    def validate_data(self, data):
        events.publish('report_validation_started', data)
        try:
            super().validate_data(data)
            events.publish('report_validation_passed', data)
        except Exception as e:
            events.publish('report_validation_failed', {'data': data, 'error': str(e)})
            raise
    
    def process_data(self, data):
        events.publish('report_processing_started', data)
        result = super().process_data(data)
        events.publish('report_processing_completed', result)
        return result
    
    def save_report(self, report):
        super().save_report(report)
        events.publish('report_saved', report)
    
    def email_report(self, report):
        super().email_report(report)  
        events.publish('report_emailed', report)

# Now you can add features without touching the core logic:
@events.on('report_validation_failed')
def handle_validation_errors(data, error):
    print(f"🔥 Validation failed: {error}")
    # Could trigger alerts, logging, etc.

@events.on('report_saved')
def backup_report(report):
    print(f"☁️ Backing up report to cloud")

@events.on('report_emailed') 
def track_delivery(report):
    shared_state.reports_sent = getattr(shared_state, 'reports_sent', 0) + 1
    print(f"📈 Reports sent this session: {shared_state.reports_sent}")

# Test it:
reporter = EventDrivenReport()
try:
    reporter.generate_report([1, 2, 3])
except:
    pass
    
events.run_for(seconds=0.5)
```

## 🧪 Testing Made Easy

Events make testing much simpler:

```python
def test_order_processing():
    events = EasyEvents()
    test_results = []
    
    # Capture events for testing
    @events.on('order_completed')
    def capture_completion(order_id, customer):
        test_results.append(('completed', order_id, customer))
    
    @events.on('email_sent')
    def capture_email(recipient):
        test_results.append(('email', recipient))
    
    # Your code under test
    @events.on('order_started') 
    def process_order(order_id, customer):
        # ... business logic ...
        events.publish('order_completed', {'order_id': order_id, 'customer': customer})
        events.publish('email_sent', customer)
    
    # Run the test
    events.publish('order_started', {'order_id': 'TEST123', 'customer': 'TestUser'})
    events.run_for(seconds=0.1)
    
    # Check results
    assert len(test_results) == 2
    assert test_results[0] == ('completed', 'TEST123', 'TestUser')
    assert test_results[1] == ('email', 'TestUser')
    print("✅ Test passed!")

test_order_processing()
```

## 💡 Key Benefits You Get

1. **Loose Coupling**: Components don't need to know about each other
2. **Easy Testing**: Test individual event handlers in isolation  
3. **Extensibility**: Add new features by subscribing to existing events
4. **Debugging**: See exactly what events fire when (use `debug=True`)
5. **Gradual Adoption**: Add events to existing code piece by piece

## 🎛️ Configuration Options

```python
# Debug mode shows all event activity
events = EasyEvents(debug=True)

# Retained events - new subscribers get recent messages
@events.on('system_status', retain=True)
def show_status(status):
    print(f"Status: {status}")

events.publish('system_status', 'healthy', retain=True)

# Later subscribers will immediately get the 'healthy' status
```

## 🚦 Common Patterns

### State Management
```python
# Use shared_state for global state
@events.on('user_login')
def track_logins(username):
    shared_state.active_users = getattr(shared_state, 'active_users', set())
    shared_state.active_users.add(username)

@events.on('user_logout')  
def track_logouts(username):
    shared_state.active_users.discard(username)
```

### Error Handling
```python
@events.on('database_error')
def handle_db_errors(error, operation):
    print(f"DB Error during {operation}: {error}")
    events.publish('send_alert', {'type': 'database', 'message': error})

@events.on('send_alert')
def alert_admin(type, message):
    print(f"🚨 ADMIN ALERT [{type}]: {message}")
```

### Batch Processing
```python
@events.every(10.0)  # Every 10 seconds
def process_batch():
    if hasattr(shared_state, 'pending_items') and shared_state.pending_items:
        events.publish('batch_ready', list(shared_state.pending_items))
        shared_state.pending_items.clear()

@events.on('item_added')
def collect_for_batch(item):
    if not hasattr(shared_state, 'pending_items'):
        shared_state.pending_items = []
    shared_state.pending_items.append(item)

@events.on('batch_ready')
def handle_batch(items):
    print(f"Processing batch of {len(items)} items")
```

## 🔧 Integration Strategies

### Strategy 1: Event Wrapper Functions
Wrap your existing functions to publish events:

```python
def with_events(func, start_event=None, end_event=None):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if start_event:
            events.publish(start_event, {'args': args, 'kwargs': kwargs})
        try:
            result = func(*args, **kwargs)
            if end_event:
                events.publish(end_event, {'result': result})
            return result
        except Exception as e:
            events.publish('error', {'function': func.__name__, 'error': str(e)})
            raise
    return wrapper

# Use it:
@with_events(start_event='calculation_started', end_event='calculation_finished')
def expensive_calculation(x, y):
    return x ** y

@events.on('calculation_started')
def log_calc_start(args, kwargs):
    print(f"🧮 Starting calculation with {args}")

expensive_calculation(2, 10)
events.run_for(seconds=0.1)
```

### Strategy 2: Class Method Decoration
Add events to specific methods in existing classes:

```python
class EventMixin:
    def __init__(self):
        self.events = EasyEvents()
    
    def event_method(self, event_name):
        def decorator(method):
            @wraps(method)
            def wrapper(*args, **kwargs):
                result = method(*args, **kwargs)
                self.events.publish(event_name, {
                    'method': method.__name__,
                    'args': args[1:],  # Skip 'self'
                    'result': result
                })
                return result
            return wrapper
        return decorator

class SmartCounter(EventMixin):
    def __init__(self):
        super().__init__()
        self.count = 0
        
        @self.events.on('count_changed')
        def log_change(method, args, result):
            print(f"Count changed by {method}: now {self.count}")
    
    @event_method('count_changed')
    def increment(self, by=1):
        self.count += by
        return self.count
    
    @event_method('count_changed') 
    def reset(self):
        self.count = 0
        return self.count

counter = SmartCounter()
counter.increment(5)
counter.increment()
counter.reset()
counter.events.run_for(seconds=0.1)
```

## 📚 Real-World Examples

### Web Scraper with Events
```python
events = EasyEvents()

@events.on('page_scraped')
def save_data(url, data):
    print(f"💾 Saving {len(data)} items from {url}")

@events.on('page_scraped')
def check_quality(url, data):
    if len(data) < 5:
        events.publish('low_quality_page', url)

@events.on('low_quality_page')
def retry_page(url):
    print(f"🔄 Marking {url} for retry")

def scrape_page(url):
    # Your scraping logic here
    data = ['item1', 'item2']  # Simulated
    events.publish('page_scraped', {'url': url, 'data': data})

scrape_page('http://example.com')
events.run_for(seconds=1)
```

### Game Event System
```python
events = EasyEvents()

@events.on('player_scored')
def update_scoreboard(player, points):
    shared_state.scores = getattr(shared_state, 'scores', {})
    shared_state.scores[player] = shared_state.scores.get(player, 0) + points
    events.publish('scoreboard_updated', shared_state.scores)

@events.on('player_scored')
def check_achievements(player, points):
    total = shared_state.scores.get(player, 0)
    if total >= 100:
        events.publish('achievement_unlocked', {'player': player, 'achievement': 'Century'})

@events.on('achievement_unlocked')
def celebrate(player, achievement):
    print(f"🏆 {player} unlocked: {achievement}!")

def player_action(player, action):
    if action == 'hit_target':
        events.publish('player_scored', {'player': player, 'points': 10})

player_action('Alice', 'hit_target')
events.run_for(seconds=0.5)
```

## 🎭 Running Modes

**1. Process for specific time:**
```python
events.run_for(seconds=2.0)  # Run for 2 seconds then stop
```

**2. Run forever (until Ctrl+C):**
```python
events.run_forever()  # Blocks until interrupted
```

**3. Background processing:**
```python
stop = events.run_in_background()
# ... do other work ...
stop()  # Stop when done
```

## ❗ Common Gotchas

1. **Events are async**: Use `run_for()` or `run_forever()` to process them
2. **Handler exceptions**: Use `debug=True` to see errors in handlers
3. **Multiple handlers**: You can have many handlers for the same event
4. **Data passing**: Events can pass dictionaries, lists, or single values

## 🎯 Next Steps

Once you're comfortable with the basics:
1. Explore the original asyncio code to understand the internals
2. Add custom event routing logic
3. Integrate with databases or APIs
4. Build distributed systems across multiple processes

The beauty is you can start simple and gradually learn the more advanced patterns as needed!