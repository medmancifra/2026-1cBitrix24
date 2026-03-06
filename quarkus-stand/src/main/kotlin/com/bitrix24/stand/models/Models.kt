package com.bitrix24.stand.models

import com.fasterxml.jackson.annotation.JsonIgnoreProperties
import com.fasterxml.jackson.annotation.JsonProperty

// ─── Bundle Status Models ───────────────────────────────────────────────────

/**
 * Liveness/health status of a Bitrix24 bundle (mini-app).
 * Returned by the vitrine panel for each registered bundle.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
data class BundleStatus(
    val bundle: String,
    val status: String,          // "healthy" | "error" | "degraded"
    val metrics: Map<String, Any> = emptyMap(),
    @JsonProperty("checked_at")
    val checkedAt: String? = null,
    val error: String? = null,
    @JsonProperty("entity_type_id")
    val entityTypeId: Int? = null
)

/**
 * Vitrine panel state — aggregates all bundle statuses.
 */
data class VitrineState(
    val bundles: List<BundleStatus>,
    val totalBundles: Int = bundles.size,
    val healthyCount: Int = bundles.count { it.status == "healthy" },
    val errorCount: Int = bundles.count { it.status == "error" },
    @JsonProperty("generated_at")
    val generatedAt: String = java.time.Instant.now().toString()
)

// ─── Kanban Models ──────────────────────────────────────────────────────────

@JsonIgnoreProperties(ignoreUnknown = true)
data class KanbanStageDto(
    val id: Int,
    val title: String,
    val sort: Int = 0,
    val color: String = "",
    @JsonProperty("task_count")
    val taskCount: Int = 0
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class KanbanCardDto(
    val id: Int,
    val title: String,
    @JsonProperty("stage_id")
    val stageId: Int,
    @JsonProperty("responsible_id")
    val responsibleId: Int? = null,
    val deadline: String? = null,
    val status: Int = 1,
    val description: String = "",
    val tags: List<String> = emptyList()
)

data class KanbanBoardDto(
    val stages: List<KanbanStageDto>,
    @JsonProperty("total_cards")
    val totalCards: Int
)

// ─── Smart Process Models ───────────────────────────────────────────────────

@JsonIgnoreProperties(ignoreUnknown = true)
data class SmartProcessTypeDto(
    val id: Int,
    @JsonProperty("entity_type_id")
    val entityTypeId: Int,
    val title: String,
    val code: String = "",
    @JsonProperty("is_use_kanban")
    val isUseKanban: Boolean = true
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class SmartItemDto(
    val id: Int,
    @JsonProperty("entity_type_id")
    val entityTypeId: Int,
    val title: String,
    @JsonProperty("stage_id")
    val stageId: String? = null,
    @JsonProperty("assigned_by_id")
    val assignedById: Int? = null,
    @JsonProperty("created_time")
    val createdTime: String? = null
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class PipelineStageDto(
    val id: Int,
    val title: String,
    val sort: Int = 0,
    val color: String = "",
    val type: String = "WORK",
    @JsonProperty("item_count")
    val itemCount: Int = 0
)

data class ProcessStateDto(
    @JsonProperty("entity_type_id")
    val entityTypeId: Int,
    @JsonProperty("total_items")
    val totalItems: Int,
    val stages: List<PipelineStageDto>,
    @JsonProperty("checked_at")
    val checkedAt: String
)

// ─── Business Process Models ─────────────────────────────────────────────────

data class WorkflowDto(
    @JsonProperty("workflow_id")
    val workflowId: String,
    @JsonProperty("template_id")
    val templateId: String? = null,
    val state: String? = null,
    @JsonProperty("started_at")
    val startedAt: String? = null
)

data class WorkflowStartRequest(
    @JsonProperty("template_id")
    val templateId: Int,
    @JsonProperty("entity_type_id")
    val entityTypeId: Int,
    @JsonProperty("item_id")
    val itemId: Int,
    val parameters: Map<String, Any> = emptyMap()
)

// ─── API Response Wrapper ────────────────────────────────────────────────────

data class ApiResponse<T>(
    val success: Boolean = true,
    val data: T? = null,
    val error: String? = null,
    val message: String? = null
) {
    companion object {
        fun <T> ok(data: T, message: String? = null) = ApiResponse(success = true, data = data, message = message)
        fun <T> error(error: String) = ApiResponse<T>(success = false, error = error)
    }
}
