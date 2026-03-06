package com.bitrix24.stand.resources

import com.bitrix24.stand.models.*
import com.bitrix24.stand.services.Bitrix24BridgeClient
import jakarta.enterprise.context.ApplicationScoped
import jakarta.inject.Inject
import jakarta.ws.rs.*
import jakarta.ws.rs.core.MediaType
import jakarta.ws.rs.core.Response
import org.eclipse.microprofile.rest.client.inject.RestClient
import org.jboss.logging.Logger

/**
 * Business Process Resource — Visual screen for BP workflow management.
 *
 * Implements Phase 2 requirement:
 * "Create, connect to operational business process chains,
 *  pause/stop, delete"
 *
 * Endpoints:
 * GET    /bp/workflows              — List all running workflows
 * POST   /bp/workflows              — Start a new workflow
 * POST   /bp/workflows/{id}/pause   — Pause a workflow
 * POST   /bp/workflows/{id}/stop    — Stop/terminate a workflow
 * DELETE /bp/workflows/{id}         — Force delete a workflow
 */
@Path("/bp")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
@ApplicationScoped
class BusinessProcessResource {

    private val log: Logger = Logger.getLogger(BusinessProcessResource::class.java)

    @Inject
    @RestClient
    lateinit var bridgeClient: Bitrix24BridgeClient

    /**
     * GET /bp/workflows
     * Lists all currently running business process workflow instances.
     */
    @GET
    @Path("/workflows")
    fun listWorkflows(): Response {
        return try {
            val workflows = bridgeClient.listWorkflows()
            Response.ok(ApiResponse.ok(workflows)).build()
        } catch (e: Exception) {
            log.errorf("Failed to list workflows: %s", e.message)
            Response.status(Response.Status.SERVICE_UNAVAILABLE)
                .entity(ApiResponse.error<List<WorkflowDto>>("Bridge unavailable: ${e.message}"))
                .build()
        }
    }

    /**
     * POST /bp/workflows
     * Starts a new business process workflow.
     * Body: {"template_id": 5, "entity_type_id": 128, "item_id": 42}
     */
    @POST
    @Path("/workflows")
    fun startWorkflow(request: WorkflowStartRequest): Response {
        if (request.templateId <= 0) {
            return Response.status(Response.Status.BAD_REQUEST)
                .entity(ApiResponse.error<String>("template_id must be a positive integer"))
                .build()
        }
        return try {
            val result = bridgeClient.startWorkflow(request)
            Response.status(Response.Status.CREATED).entity(result).build()
        } catch (e: Exception) {
            log.errorf("Failed to start workflow: %s", e.message)
            Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity(ApiResponse.error<String>("Failed to start workflow: ${e.message}"))
                .build()
        }
    }

    /**
     * POST /bp/workflows/{workflowId}/pause
     * Pauses a running workflow (остановка-пауза).
     */
    @POST
    @Path("/workflows/{workflowId}/pause")
    fun pauseWorkflow(@PathParam("workflowId") workflowId: String): Response {
        return try {
            val result = bridgeClient.pauseWorkflow(workflowId)
            Response.ok(result).build()
        } catch (e: Exception) {
            log.errorf("Failed to pause workflow %s: %s", workflowId, e.message)
            Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity(ApiResponse.error<Boolean>("Failed to pause: ${e.message}"))
                .build()
        }
    }

    /**
     * POST /bp/workflows/{workflowId}/stop
     * Terminates a running workflow (остановка).
     */
    @POST
    @Path("/workflows/{workflowId}/stop")
    fun stopWorkflow(@PathParam("workflowId") workflowId: String): Response {
        return try {
            val result = bridgeClient.stopWorkflow(workflowId)
            Response.ok(result).build()
        } catch (e: Exception) {
            log.errorf("Failed to stop workflow %s: %s", workflowId, e.message)
            Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity(ApiResponse.error<Boolean>("Failed to stop: ${e.message}"))
                .build()
        }
    }

    /**
     * DELETE /bp/workflows/{workflowId}
     * Force deletes a workflow instance (удаление).
     */
    @DELETE
    @Path("/workflows/{workflowId}")
    fun deleteWorkflow(@PathParam("workflowId") workflowId: String): Response {
        return try {
            val result = bridgeClient.deleteWorkflow(workflowId)
            Response.ok(result).build()
        } catch (e: Exception) {
            log.errorf("Failed to delete workflow %s: %s", workflowId, e.message)
            Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity(ApiResponse.error<Boolean>("Failed to delete: ${e.message}"))
                .build()
        }
    }
}
