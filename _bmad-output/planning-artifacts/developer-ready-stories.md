---
title: Church Management System Developer-Ready Stories
status: draft
created: 2026-06-29
updated: 2026-06-29
---

# Developer-Ready Stories

## Story 1: Member and Division Management
### 1.1 Create and update member records
- As an administrator, I want to create and update member records so the church directory stays accurate.
- Acceptance Criteria:
  - The system provides a form for creating a new member record.
  - Required fields include name, contact info, household, status, and division assignment.
  - Existing records can be edited and updated from the member profile.
  - Changes are persisted in the shared member data store.
- Implementation Notes:
  - Build a `Member` model with fields for personal details, contact info, household link, and division.
  - Expose create/edit endpoints in the backend API.
  - Add UI forms for create/edit flows with validation.

### 1.2 Assign members to divisions
- As a church administrator, I want to assign members to divisions such as Sunday School, Youth, and Adult classes so ministry groups are organized.
- Acceptance Criteria:
  - The member profile supports selecting one or more divisions.
  - Division categories include Sunday School, Youth, and Adult class.
  - The selected division appears on the member profile and directory listings.
- Implementation Notes:
  - Use a `Division` lookup table or enum.
  - Support many-to-many or one-to-many assignment depending on requirements.
  - Add division filter support to member search.

### 1.3 Search and filter member directory
- As a staff member, I want to search and filter members so I can find people quickly.
- Acceptance Criteria:
  - Users can search by name or household.
  - Users can filter by status, tag, division, or active/inactive.
  - Search results display matching members with their divisions.
- Implementation Notes:
  - Implement search API with query parameters.
  - Add directory UI with filters and results.

## Story 2: Attendance and Class Tracking
### 2.1 Record attendance for services and events
- As a ministry leader, I want to record attendance so participation can be tracked over time.
- Acceptance Criteria:
  - Attendance is recorded for a person, event, or service date.
  - Attendance entries include date, person, and event/class context.
  - Attendance history is visible for individuals and groups.
- Implementation Notes:
  - Build `AttendanceRecord` with person, date, and event/division links.
  - Add API and UI for attendance entry and history.

### 2.2 Track attendance by division
- As a class leader, I want to track attendance by division so Sunday School, Youth, and Adult class participation is visible.
- Acceptance Criteria:
  - Attendance can be attributed to a specific division.
  - Division attendance summaries are viewable by date and class.
  - Leaders can compare participation across divisions.
- Implementation Notes:
  - Add division field to attendance records.
  - Create summary report endpoints per division.

### 2.3 Manage event RSVPs
- As an event coordinator, I want to track RSVPs so I can plan events more effectively.
- Acceptance Criteria:
  - Events can be created with date, location, and description.
  - People can be marked as attending or not attending.
  - Event attendee counts are visible.
- Implementation Notes:
  - Create `Event` and `EventRSVP` entities.
  - Add event management UI and RSVP tracking.

## Story 3: Giving and Fundraising
### 3.1 Record donations
- As an administrator, I want to record donations so giving history is maintained.
- Acceptance Criteria:
  - Donations can be entered for a person or household.
  - Donation records store amount, date, and donation type.
  - Donation history is viewable for the donor.
- Implementation Notes:
  - Build `Donation` model with link to person/household.
  - Add donation entry and history views.

### 3.2 Track building fundraising campaigns
- As a church leader, I want to track fundraising campaigns for the church building so progress toward completion is visible.
- Acceptance Criteria:
  - A fundraising campaign can be created for the building project.
  - Pledges and contributions can be recorded against the campaign.
  - Progress toward campaign target is visible in summary reports.
- Implementation Notes:
  - Add `FundraisingCampaign` and `Pledge` entities.
  - Link donations to campaigns.
  - Add campaign progress dashboard.

### 3.3 Display giving and fundraising summaries
- As a church leader, I want to review giving summaries so I can monitor stewardship trends.
- Acceptance Criteria:
  - Summaries show totals by period or donor.
  - Reports can be exported or reviewed by staff.
  - Fundraising campaign progress is shown alongside general giving.
- Implementation Notes:
  - Build reporting endpoints for giving summaries.
  - Add dashboards with export capabilities.

## Story 4: Communication and Reporting
### 4.1 Send targeted announcements
- As a staff member, I want to send announcements so members receive timely updates.
- Acceptance Criteria:
  - Messages can be composed and sent to selected groups.
  - Audience filters include tag, ministry, division, or household.
  - Sent messages are logged in the system.
- Implementation Notes:
  - Create messaging model and UI.
  - Support target group selection and message logging.

### 4.2 Provide basic dashboards
- As a leader, I want dashboards for attendance, giving, and fundraising so I can see key metrics.
- Acceptance Criteria:
  - Dashboards show attendance trends, giving totals, and campaign progress.
  - Dashboards are accessible to authorized roles.
- Implementation Notes:
  - Build summary views and charts from the shared data model.

### 4.3 Export summary reports
- As a staff member, I want to export summary reports for leadership review.
- Acceptance Criteria:
  - Reports can be exported to CSV or PDF.
  - Export content includes attendance, giving, and fundraising summaries.
- Implementation Notes:
  - Implement export endpoints and UI actions.
