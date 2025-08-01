# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Project Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Database setup
python manage.py migrate
python manage.py init_ncs_competencies  # Initialize NCS competency data
python manage.py create_student_data    # Generate test data (optional)

# Create superuser
python manage.py createsuperuser
```

### Development Server
```bash
# Run development server
python manage.py runserver

# Run on specific port
python manage.py runserver 8080
```

### Database Operations
```bash
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (careful!)
rm db.sqlite3
python manage.py migrate
```

### Custom Management Commands
```bash
# Initialize NCS competencies (required for NCS functionality)
python manage.py init_ncs_competencies

# Generate test student data
python manage.py create_student_data
```

### Testing
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test teacher
python manage.py test student
python manage.py test ncs
```

## Project Architecture

### Core Django Structure
- **Framework**: Django 5.2.1
- **Database**: SQLite3 (development)
- **Settings**: Located in `config/settings.py`
- **Root URLs**: Located in `config/urls.py`
- **Language**: Korean (ko-kr) with Korean comments and UI

### Application Architecture (8 Main Apps)

#### 1. **accounts** - Authentication & School Management
- Multi-role user system (Teacher, Student, Admin)
- School, Class, and user hierarchy management
- Role-based access control throughout the platform

#### 2. **teacher** - Course Management Hub
- Hierarchical course structure: Course → Chapter → SubChapter → Chasi → Slides
- Rich content creation with multiple content types
- File attachment system with temporary upload handling
- Course assignment to classes and individual students
- Statistical analysis and student progress tracking

#### 3. **student** - Learning Interface
- Slide-by-slide progress tracking
- Answer submission and note-taking
- Physical activity recording
- Personal learning analytics dashboard

#### 4. **ncs** - National Competency Standards
- NCS competency mapping and assessment
- Adaptive learning sessions with retry logic
- Comprehensive weakness analysis
- Class-wide statistics and individual progress
- **Critical**: Requires `init_ncs_competencies` command to function

#### 5. **new_cp** - Content Templates
- Reusable content templates
- AI-powered content generation integration
- Template management system

#### 6. **super_agent** - AI Question Generation
- Google Gemini AI integration for question generation
- JSON-based question processing
- HTML template generation for assessments
- Competency-based content tagging

#### 7. **rolling** - Physical Education Assessment
- Specialized physical education (rolling/tumbling) tracking
- Multi-attempt evaluation system
- Teacher feedback and scoring

#### 8. **app_home** - Health Habit Tracking
- Student wellness tracking (6-promise system)
- Daily reflection journals
- Teacher evaluation and badge system

#### 9. **physical_education** - Physical Education app (PAPS)
- Handle physical education system
- Teacher PAPS management system

### Key Integration Points

#### AI Integration
- **Google Gemini API**: Configured via `GEMINI_API_KEY` environment variable
- **Content Generation**: Automated question creation and template generation
- **Processing**: JSON-based content processing for educational materials

#### Authentication Flow
- Landing page at root (`/`)
- Role-based redirect: Teachers → `/teacher/dashboard`, Students → `/student/dashboard`
- Login required for all authenticated views

#### File Management
- **Media Files**: Organized by content type with date-based structure
- **Static Files**: Separated by application in `static/` directory
- **Attachments**: Temporary upload handling with file validation

### Development Workflow Patterns

#### Content Creation Flow
1. Teachers create courses with hierarchical structure
2. Content is created using templates or AI generation
3. Files are uploaded and processed
4. Content is assigned to classes/students
5. Student progress is tracked granularly

#### Assessment Flow
1. NCS competencies are mapped to content
2. Questions are generated (manually or via AI)
3. Students complete assessments
4. Results are analyzed for weaknesses
5. Adaptive learning paths are suggested

### Critical Configuration Notes

#### Environment Variables
- `GEMINI_API_KEY`: Required for AI features
- `DEBUG`: Currently True for development
- `SECRET_KEY`: Django secret key (should be changed for production)

#### Database Considerations
- Uses SQLite3 for development
- Migration files are committed and should be applied
- Custom management commands initialize required data

#### Security Settings
- CSRF protection enabled
- Session management configured
- File upload restrictions in place
- DEBUG mode includes detailed logging

### File Organization Patterns
- Korean comments and documentation throughout
- Templates organized by app in `templates/` directory
- Static assets separated by functionality
- Media files organized by upload date and content type

### Common Gotchas
- NCS functionality requires running `init_ncs_competencies` command
- AI features require valid Google Gemini API key
- Korean language settings affect admin interface
- File uploads have size restrictions (10MB default)
- Some middleware temporarily disabled for debugging (check settings)

## Critical Rules - DO NOT VIOLATE

- **NEVER create mock data or simplified components** unless explicitly told to do so

- **NEVER replace existing complex components with simplified versions** - always fix the actual problem

- **ALWAYS work with the existing codebase** - do not create new simplified alternatives

- **ALWAYS find and fix the root cause** of issues instead of creating workarounds

- When debugging issues, focus on fixing the existing implementation, not replacing it

- When something doesn't work, debug and fix it - don't start over with a simple version

- **ALWAYS check Tabulator DOCS before making changes** to Tabulator-related components - they have breaking changes


## 1. Non-negotiable golden rules

| #: | AI *may* do                                                            | AI *must NOT* do                                                                    |
|---|------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| G-0 | Whenever unsure about something that's related to the project, ask the developer for clarification before making changes.    |  ❌ Write changes or use tools when you are not sure about something project specific, or if you don't have context for a particular feature/decision. |
| G-1 | For changes >300 LOC or >3 files, **ask for confirmation**.            | ❌ Refactor large modules without human guidance.                                     |
| G-2 | Stay within the current task context. Inform the dev if it'd be better to start afresh.                                  | ❌ Continue work from a prior prompt after "new task" – start a fresh session.      |

---