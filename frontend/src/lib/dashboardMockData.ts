interface PersonalStats {
  issues_solved: number;
  prs_merged: number;
  total_xp: number;
  streak_days: number;
  longest_streak: number;
  rank: number;
  earned_badges: string[];
  available_points: number;
  unused_freezes: number;
}

interface AssignedIssue {
  id: number;
  points: number;
  title: string;
  description?: string;
  status?: string;
  created_at?: string;
}

interface ContributorDashboardData {
  personal_stats: PersonalStats;
  assigned_issues: AssignedIssue[];
}

const mockPersonalStats: PersonalStats = {
  issues_solved: 12,
  prs_merged: 8,
  total_xp: 2840,
  streak_days: 14,
  longest_streak: 21,
  rank: 3,
  earned_badges: ["first-pr", "streak-7", "streak-14", "bug-hunter"],
  available_points: 2840,
  unused_freezes: 2,
};

const mockAssignedIssues: AssignedIssue[] = [
  {
    id: 101,
    points: 150,
    title: "Add dark mode toggle to settings page",
    description: "Implement a theme switcher component",
    status: "in_progress",
    created_at: "2026-07-01T10:00:00Z",
  },
  {
    id: 102,
    points: 200,
    title: "Fix pagination on leaderboard",
    description: "Leaderboard page doesn't paginate correctly",
    status: "open",
    created_at: "2026-07-05T14:30:00Z",
  },
  {
    id: 103,
    points: 100,
    title: "Add input validation to contact form",
    description: "Sanitize user inputs on the contact form",
    status: "review",
    created_at: "2026-07-08T09:15:00Z",
  },
  {
    id: 104,
    points: 300,
    title: "Optimize database queries for feed page",
    description: "Reduce N+1 queries on the activity feed",
    status: "open",
    created_at: "2026-07-10T16:45:00Z",
  },
];

export const mockDashboardData: ContributorDashboardData = {
  personal_stats: mockPersonalStats,
  assigned_issues: mockAssignedIssues,
};
