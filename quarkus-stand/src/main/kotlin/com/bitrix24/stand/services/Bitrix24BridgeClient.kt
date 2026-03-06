package com.bitrix24.stand.services

import com.bitrix24.stand.models.*
import jakarta.enterprise.context.ApplicationScoped
import jakarta.ws.rs.core.Response
import org.eclipse.microprofile.config.inject.ConfigProperty
import org.eclipse.microprofile.rest.client.inject.RegisterRestClient
import jakarta.ws.rs.*
import jakarta.ws.rs.core.MediaType

/**
 * REST client interface for calling the Bitrix24 Python boilerplate bridge.
 *
 * The Python boilerplate (core + bundles) exposes a simple HTTP bridge API
 * that this Quarkus microservice calls to retrieve and manipulate Bitrix24 data.
 *
 * In a real deployment:
 * - Python boilerplate runs as a sidecar or separate service
 * - Quarkus stand calls it via HTTP to display visual screens
 */
@RegisterRestClient(configKey = "bitrix24-bridge")
@Path("/api/v1")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
interface Bitrix24BridgeClient {

    @GET
    @Path("/health")
    fun getHealth(): Response

    @GET
    @Path("/bundles/status")
    fun getAllBundleStatuses(): List<BundleStatus>

    @GET
    @Path("/kanban/{entityType}/board")
    fun getKanbanBoard(@PathParam("entityType") entityType: Int): KanbanBoardDto

    @POST
    @Path("/kanban/{entityType}/cards/{taskId}/move")
    fun moveKanbanCard(
        @PathParam("entityType") entityType: Int,
        @PathParam("taskId") taskId: Int,
        @QueryParam("stage_id") stageId: Int
    ): ApiResponse<Boolean>

    @GET
    @Path("/smart/{entityTypeId}/state")
    fun getSmartProcessState(@PathParam("entityTypeId") entityTypeId: Int): ProcessStateDto

    @GET
    @Path("/smart/types")
    fun listSmartProcessTypes(): List<SmartProcessTypeDto>

    @POST
    @Path("/smart/{entityTypeId}/items")
    fun addSmartItem(
        @PathParam("entityTypeId") entityTypeId: Int,
        body: Map<String, Any>
    ): SmartItemDto

    @POST
    @Path("/smart/{entityTypeId}/items/{itemId}/move")
    fun moveSmartItem(
        @PathParam("entityTypeId") entityTypeId: Int,
        @PathParam("itemId") itemId: Int,
        @QueryParam("stage_id") stageId: String
    ): ApiResponse<Boolean>

    @GET
    @Path("/bp/workflows")
    fun listWorkflows(): List<WorkflowDto>

    @POST
    @Path("/bp/workflows/start")
    fun startWorkflow(request: WorkflowStartRequest): ApiResponse<String>

    @POST
    @Path("/bp/workflows/{workflowId}/pause")
    fun pauseWorkflow(@PathParam("workflowId") workflowId: String): ApiResponse<Boolean>

    @POST
    @Path("/bp/workflows/{workflowId}/stop")
    fun stopWorkflow(@PathParam("workflowId") workflowId: String): ApiResponse<Boolean>

    @DELETE
    @Path("/bp/workflows/{workflowId}")
    fun deleteWorkflow(@PathParam("workflowId") workflowId: String): ApiResponse<Boolean>
}
