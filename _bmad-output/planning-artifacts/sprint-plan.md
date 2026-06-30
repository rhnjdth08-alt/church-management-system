---
title: Church Management System MVP Sprint Plan
status: draft
created: 2026-06-29
updated: 2026-06-29
---

# Sprint Plan

## Sprint Goal
Deliver the core church management MVP for member/division management, attendance tracking, giving/fundraising, and basic communication so the staff can begin using the system for day-to-day administration and building completion fundraising.

## Sprint Duration
2 weeks (10 working days)

## Priority Workstreams
- Member and Division Management
- Attendance and Class Tracking
- Giving and Fundraising
- Communication and Reporting

## Sprint Backlog
### 1. Member and Division Management
- Story 1.1: Create and update member records
- Story 1.2: Assign members to divisions (Sunday School, Youth, Adult classes)
- Story 1.3: Search and filter the directory by division, status, and tags

### 2. Attendance and Class Tracking
- Story 2.1: Record attendance for services and events
- Story 2.2: Track attendance by division and compare class participation
- Story 2.3: Manage event RSVPs and attendee counts

### 3. Giving and Fundraising
- Story 3.1: Record donations by person or household
- Story 3.2: Track fundraising campaigns for the church building
- Story 3.3: Display giving and fundraising progress summaries

### 4. Communication and Reporting
- Story 4.1: Send announcements and follow-up messages to groups
- Story 4.2: Provide basic dashboards for attendance, giving, and fundraising
- Story 4.3: Export summary reports for leadership review

## MVP Acceptance Criteria
- The system records members, households, and division assignments reliably.
- Attendance is captured for services, events, and class divisions.
- Donations and fundraising progress can be entered and summarized.
- Staff can send targeted communications to groups and review key metrics.
- The initial architecture supports extension into additional ministry and reporting needs.

## Risks and Mitigations
- Risk: Overloading the first sprint with too many reporting requirements.
  - Mitigation: Focus on core capture workflows first, add only essential summary dashboards.
- Risk: Division tracking for classes may require more detailed role behavior than planned.
  - Mitigation: Keep class attendance workflows simple and extendable.
- Risk: Fundraising campaign workflows may need additional pledge management.
  - Mitigation: Build the campaign structure first; add pledge detail in a follow-on sprint if needed.

## Next Recommended Step
1. Finalize the MVP stories in a sprint backlog tool or project board.
2. Begin implementation with member/division management and attendance capture.
3. Use `bmad-create-story` or `bmad-sprint-planning` next to turn these stories into developer-ready tasks.
