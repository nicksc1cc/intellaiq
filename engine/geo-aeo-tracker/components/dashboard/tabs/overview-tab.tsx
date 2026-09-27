import { VisibilityAnalyticsTab } from "./visibility-analytics-tab";

/**
 * Overview — the first destination when opening IntellaIQ.
 * Displays a high-level summary of AI visibility for the workspace.
 */
export function OverviewTab({ data, runs }: { data: any; runs: any[] }) {
  return <VisibilityAnalyticsTab data={data} runs={runs} />;
}