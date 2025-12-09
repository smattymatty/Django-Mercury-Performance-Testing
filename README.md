# Django Mercury

[![PyPI version](https://badge.fury.io/py/django-mercury-performance.svg)](https://badge.fury.io/py/django-mercury-performance)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Django 3.2-5.1](https://img.shields.io/badge/django-3.2--5.1-green.svg)](https://docs.djangoproject.com/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-red.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Built for: EduLite](https://img.shields.io/badge/Built%20for-EduLite-orange)](https://github.com/ibrahim-sisar/EduLite)
[![Values: Open](https://img.shields.io/badge/Values-Open%20%7C%20Free%20%7C%20Fair-purple)](https://github.com/80-20-Human-In-The-Loop)

**Part of the [80-20 Human in the Loop](https://github.com/80-20-Human-In-The-Loop) ecosystem**

> **Test Django app speed. Learn why it's slow. Fix it.**

Django Mercury is a performance testing framework that adapts to your experience level - teaching beginners, empowering experts, and enabling automation while preserving human understanding.

## ⚡ Quick Start

### Install
```bash
pip install django-mercury-performance
```

### Choose Your Profile

Mercury adapts to three audiences through its plugin system:

```bash
# 🎓 Students - Learn while testing
mercury-test --profile student

# 💼 Experts - Fast and efficient
mercury-test --profile expert

# 🤖 Agents - Structured output for CI/CD
mercury-test --profile agent
```

### Write Your First Test

```python
# For investigation and learning
from django_mercury import DjangoMercuryAPITestCase

class QuickCheck(DjangoMercuryAPITestCase):
    """Mercury automatically monitors all tests in this class."""
    
    def test_user_api(self):
        response = self.client.get('/api/users/')
        # Mercury detects issues and explains them!

# For production with specific assertions
from django_mercury import DjangoPerformanceAPITestCase
from django_mercury import monitor_django_view

class ProductionTests(DjangoPerformanceAPITestCase):
    """Enforce performance standards."""
    
    def test_user_api_performance(self):
        with monitor_django_view("user_api") as monitor:
            response = self.client.get('/api/users/')
        
        self.assertResponseTimeLess(monitor, 100)  # Must be under 100ms
        self.assertQueriesLess(monitor, 10)        # Max 10 queries
        self.assertNoNPlusOne(monitor)             # No N+1 patterns
```

## 🔌 Plugin Architecture

Mercury uses a **small core, big plugin** design that enables different experiences:

```bash
mercury-test --list-plugins

Available Plugins:
✅ discovery - Smart Django project finding
✅ wizard - Interactive test selection (students)
✅ learn - Quizzes and tutorials (students)
✅ hints - Performance tips (students)
```

Each profile automatically configures the right plugins:
- **Student**: All educational plugins enabled
- **Expert**: Minimal plugins for speed
- **Agent**: Non-interactive with JSON output

[Learn more about the plugin system →](https://github.com/80-20-Human-In-The-Loop/Django-Mercury-Performance-Testing/wiki/Why-Plugins)

## 📊 What Mercury Shows You

### 🎓 Student Mode - Educational Output
```
📚 LEARNING MOMENT DETECTED
═══════════════════════════════════════════════════════
Found: N+1 Query Pattern
Location: UserSerializer.get_profile_data()

📖 What's happening:
Your code makes 1 query to get users, then 1 query
per user to get profiles. With 100 users = 101 queries!

💡 Why this matters:
Each query adds ~2ms overhead. This gets slower as
your data grows.

🔧 How to fix:
Add .select_related('profile') to your queryset:
  User.objects.select_related('profile').all()

📚 Want to learn more?
Run: mercury-test --learn n1-queries
```

### 💼 Expert Mode - Concise Results
```
test_user_list     156ms  45q  23MB  ⚠️ N+1@L45  SLOW
test_user_detail    23ms   3q  12MB  ✅         PASS

Critical: N+1 in views.py:45. Fix: select_related('profile')
```

### 🤖 Agent Mode - Structured JSON
```json
{
  "test": "test_user_list",
  "metrics": {
    "response_time_ms": 156,
    "queries": 45,
    "memory_mb": 23
  },
  "issues": [{
    "type": "n_plus_one",
    "severity": "high",
    "location": "views.py:45",
    "auto_fixable": false,
    "requires_human_review": true
  }]
}
```

## 🎓 Educational Features

Mercury doesn't just find problems - it teaches you to understand them:

### Interactive Learning
```bash
# Start learning mode
mercury-test --learn

# Take quizzes
mercury-test --learn --quiz

# Get step-by-step tutorials
mercury-test --learn n1-queries
```

### Progress Tracking
```bash
mercury-test --learn --progress

📊 YOUR PROGRESS
═══════════════════════════════════════
Level: Intermediate (750 XP)
Topics Mastered: N+1 Queries ✅, Indexing ✅
Currently Learning: Caching (70%)
Next Goal: Complete Caching module
```

### Real-time Teaching
When Mercury finds issues, it explains them in context, shows why they matter, and teaches you how to fix them.

## 🚀 Performance Grading

Mercury grades your application's performance:

| Grade | Score | Meaning |
|-------|-------|---------|
| **S** | 100 | Perfect performance |
| **A+** | 95-99 | Excellent |
| **A** | 90-94 | Very good |
| **B** | 80-89 | Good |
| **C** | 70-79 | Acceptable |
| **D** | 60-69 | Poor |
| **F** | <60 | Failing |

## 🛠️ CI/CD Integration

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Mercury Tests
        run: |
          pip install django-mercury-performance
          mercury-test --profile agent --export-metrics=json
      - name: Check Performance
        run: |
          python -c "import json; exit(0 if json.load(open('metrics.json'))['grade'] >= 'B' else 1)"
```

## 📚 Documentation

- **[Quick Start Guide](https://github.com/80-20-Human-In-The-Loop/Django-Mercury-Performance-Testing/wiki/Quick-Start)** - Get running in 5 minutes
- **[Educational Mode](https://github.com/80-20-Human-In-The-Loop/Django-Mercury-Performance-Testing/wiki/Educational-Mode)** - Learn performance optimization
- **[Understanding Reports](https://github.com/80-20-Human-In-The-Loop/Django-Mercury-Performance-Testing/wiki/Understanding-Reports)** - Interpret Mercury's output
- **[Plugin System](https://github.com/80-20-Human-In-The-Loop/Django-Mercury-Performance-Testing/wiki/Why-Plugins)** - Extend Mercury's capabilities
- **[API Reference](https://github.com/80-20-Human-In-The-Loop/Django-Mercury-Performance-Testing/wiki/API-Reference)** - Complete API documentation

## 🤝 Contributing

Mercury is part of the [80-20 Human-in-the-Loop](https://github.com/80-20-Human-In-The-Loop) ecosystem. We welcome contributions from everyone!

### Our Values
- **Education First**: Tools should teach, not just detect
- **Human Understanding**: Preserve human decision-making
- **Open Community**: Built together, shared freely

### How to Contribute
1. **Use Mercury** - Test it on your projects
2. **Report Issues** - Help us improve
3. **Share Knowledge** - Write tutorials, create quizzes
4. **Code** - Fix bugs, add features
5. **Translate** - Make Mercury accessible globally

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 🚧 Roadmap

### Current (v1.0)
- ✅ Three-audience plugin system
- ✅ Educational mode with quizzes
- ✅ Performance grading system
- ✅ N+1 detection
- ✅ Smart project discovery

### Next (v1.1)
- 🔨 MCP server for AI integration
- 🔨 Performance trend tracking
- 🔨 Custom plugin API
- 🔨 More educational content

### Future (v2.0)
- 🤖 AI-assisted optimization
- 🤖 Auto-fix for simple issues
- 🤖 Performance prediction
- 🤖 Team learning features

## 📄 License

GNU General Public License v3.0 (GPL-3.0)

We chose GPL to ensure Mercury remains:
- **Free** - No barriers to learning
- **Open** - Transparent development
- **Fair** - Improvements benefit everyone

## 🙏 Acknowledgments

- **[EduLite](https://github.com/ibrahim-sisar/EduLite)** - Where Mercury was born
- **[80-20 Human-in-the-Loop](https://github.com/80-20-Human-In-The-Loop)** - For the philosophy
- **Django Community** - For the amazing framework
- **You** - For making Django apps faster!

---

<div align="center">

**Mercury: Making performance testing educational, accessible, and effective.**

*Because every developer deserves to understand their code's performance.*

[Get Started](https://github.com/80-20-Human-In-The-Loop/Django-Mercury-Performance-Testing/wiki/Quick-Start) • [Documentation](https://github.com/80-20-Human-In-The-Loop/Django-Mercury-Performance-Testing/wiki) • [Community](https://github.com/80-20-Human-In-The-Loop/Community)

</div>