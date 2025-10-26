#!/usr/bin/env node
import { writeFileSync } from 'fs';

// Complete inventory of all MCP tools
const mcpTools = {
  "memory-unified": [
    "get_unified_context",
    "search_unified_memory",
    "create_unified_entities",
    "sync_conversation_state"
  ],
  "github": [
    "create_or_update_file", "search_repositories", "create_repository",
    "get_file_contents", "push_files", "create_issue", "create_pull_request",
    "fork_repository", "create_branch", "list_commits", "list_issues",
    "update_issue", "add_issue_comment", "search_code", "search_issues",
    "search_users", "get_issue", "get_pull_request", "list_pull_requests",
    "create_pull_request_review", "merge_pull_request", "get_pull_request_files",
    "get_pull_request_status", "update_pull_request_branch", "get_pull_request_comments",
    "get_pull_request_reviews"
  ],
  "filesystem": [
    "read_file", "read_text_file", "read_media_file", "read_multiple_files",
    "write_file", "edit_file", "create_directory", "list_directory",
    "list_directory_with_sizes", "directory_tree", "move_file", "search_files",
    "get_file_info"
  ],
  "apify": [
    "fetch-actor-details", "search-actors", "call-actor", "search-apify-docs",
    "fetch-apify-docs", "apify-slash-rag-web-browser", "get-actor-output"
  ],
  "airbnb": ["airbnb_search", "airbnb_listing_details"],
  "pdf-tools": ["extract_text", "fill_pdf_form", "get_pdf_form_elements"],
  "mac-control": ["applescript_execute"],
  "everything": [
    "echo", "add", "longRunningOperation", "printEnv", "sampleLLM",
    "getTinyImage", "annotatedMessage", "getResourceReference", "getResourceLinks",
    "structuredContent", "listRoots"
  ],
  "xero": [
    "delete-timesheet", "get-timesheet", "create-contact", "create-credit-note",
    "create-manual-journal", "create-invoice", "create-quote", "create-payment",
    "create-item", "create-bank-transaction", "create-timesheet", "create-tracking-category",
    "create-tracking-options", "list-accounts", "list-contacts", "list-credit-notes",
    "list-invoices", "list-items", "list-manual-journals", "list-quotes",
    "list-tax-rates", "list-trial-balance", "list-payments", "list-profit-and-loss",
    "list-bank-transactions", "list-payroll-employees", "list-report-balance-sheet",
    "list-organisation-details", "list-payroll-employee-leave", "list-payroll-leave-periods",
    "list-payroll-employee-leave-types", "list-payroll-employee-leave-balances",
    "list-payroll-leave-types", "list-aged-receivables-by-contact", "list-aged-payables-by-contact",
    "list-timesheets", "list-contact-groups", "list-tracking-categories", "update-contact",
    "update-credit-note", "update-invoice", "update-manual-journal", "update-quote",
    "update-item", "update-bank-transaction", "approve-timesheet", "add-timesheet-line",
    "update-timesheet-line", "revert-timesheet", "update-tracking-category", "update-tracking-options"
  ],
  "perplexity": ["perplexity_ask", "perplexity_research", "perplexity_reason", "perplexity_search"],
  "cloud-run": [
    "list_projects", "create_project", "list_services", "get_service",
    "get_service_log", "deploy_local_folder", "deploy_file_contents", "deploy_container_image"
  ],
  "deepseek": ["chat_completion", "multi_turn_chat"],
  "mcp-files": ["read_symbol", "insert_text", "os_notification"],
  "mcp-tasks": ["tasks_setup", "tasks_search", "tasks_add", "tasks_update", "tasks_summary"],
  "todoist": ["todoist_api"],
  "transcribe": ["get-balance", "convert-to-text", "read-transcriptions", "update-transcription"],
  "time": ["get_current_time", "convert_time"],
  "think-mcp": ["think"],
  "google-workspace": [
    "list_calendars", "get_events", "create_event", "modify_event", "get_messages",
    "send_message", "search_messages", "get_doc_content", "create_doc", "modify_doc_text",
    "search_drive_files", "get_drive_file_content", "create_drive_file", "create_form",
    "get_form", "search_gmail_messages", "get_gmail_message_content", "get_gmail_messages_content_batch",
    "send_gmail_message", "search_custom", "read_sheet_values", "modify_sheet_values",
    "create_spreadsheet", "create_presentation", "get_presentation", "list_tasks",
    "get_task", "create_task", "update_task"
  ],
  "pushover": ["send"],
  "gmail-advanced": [
    "send_email", "draft_email", "read_email", "search_emails", "modify_email",
    "delete_email", "list_email_labels", "batch_modify_emails", "batch_delete_emails",
    "create_label", "update_label", "delete_label", "get_or_create_label", "create_filter",
    "list_filters", "get_filter", "delete_filter", "create_filter_from_template",
    "download_attachment"
  ],
  "memory": [
    "create_entities", "create_relations", "add_observations", "delete_entities",
    "delete_observations", "delete_relations", "read_graph", "search_nodes", "open_nodes"
  ],
  "twilio": ["send_whatsapp"],
  "context7": ["resolve-library-id", "get-library-docs"]
};

// Count total tools
const allTools = [];
Object.entries(mcpTools).forEach(([server, tools]) => {
  tools.forEach(tool => {
    allTools.push({ server, tool });
  });
});

console.log(`\n📊 MCP Tool Inventory`);
console.log(`==================`);
console.log(`Total Servers: ${Object.keys(mcpTools).length}`);
console.log(`Total Tools: ${allTools.length}`);

// Calculate 33% sample
const sampleSize = Math.ceil(allTools.length * 0.33);
console.log(`\n🎯 Random Sample Selection`);
console.log(`Sample Size (33%): ${sampleSize} tools`);

// Shuffle and select random sample
const shuffled = allTools.sort(() => Math.random() - 0.5);
const sample = shuffled.slice(0, sampleSize);

// Group by server
const sampleByServer = {};
sample.forEach(({ server, tool }) => {
  if (!sampleByServer[server]) {
    sampleByServer[server] = [];
  }
  sampleByServer[server].push(tool);
});

console.log(`\n📋 Selected Tools for Testing (${sample.length} tools)`);
console.log(`==================\n`);

Object.entries(sampleByServer).sort().forEach(([server, tools]) => {
  console.log(`${server} (${tools.length} tools):`);
  tools.forEach(tool => {
    console.log(`  - ${tool}`);
  });
  console.log();
});

// Export as JSON for processing
const output = {
  total_tools: allTools.length,
  sample_size: sampleSize,
  sample_percentage: 33,
  selected_tools: sample,
  by_server: sampleByServer
};

console.log(`\n💾 Saving to test_sample.json...`);
writeFileSync(
  'test_sample.json',
  JSON.stringify(output, null, 2)
);
console.log(`✅ Done!\n`);
