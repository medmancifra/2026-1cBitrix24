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
 * Smart Process Resource — Visual screen for Smart Process management.
 *
 * Implements Phase 2 requirement:
 * "Generate visual screens — creation, connection to operational
 *  business process chains, pause/stop, delete"
 *
 * Use-case story (real company):
 * A service desk manages "Service Requests" as a Smart Process.
 * Each request moves through: New → In Progress → In Review → Done/Cancelled.
 * Business processes can be started on each item for automated notifications.
 *
 * Endpoints:
 * GET  /smart/types                     — List all smart process types
 * GET  /smart/{entityTypeId}/state      — Full process state (stages + items)
 * POST /smart/{entityTypeId}/items      — Create new item
 * POST /smart/{entityTypeId}/items/{id}/move — Move item to stage
 */
@Path("/smart")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
@ApplicationScoped
class SmartProcessResource {

    private val log: Logger = Logger.getLogger(SmartProcessResource::class.java)

    @Inject
    @RestClient
    lateinit var bridgeClient: Bitrix24BridgeClient

    /**
     * GET /smart/types
     * Lists all Smart Process types (custom entity types) defined in the portal.
     */
    @GET
    @Path("/types")
    fun listTypes(): Response {
        return try {
            val types = bridgeClient.listSmartProcessTypes()
            Response.ok(ApiResponse.ok(types)).build()
        } catch (e: Exception) {
            log.errorf("Failed to list smart process types: %s", e.message)
            Response.status(Response.Status.SERVICE_UNAVAILABLE)
                .entity(ApiResponse.error<List<SmartProcessTypeDto>>("Bridge unavailable: ${e.message}"))
                .build()
        }
    }

    /**
     * GET /smart/{entityTypeId}/state
     * Returns full state of a Smart Process: stages with item counts.
     */
    @GET
    @Path("/{entityTypeId}/state")
    fun getState(@PathParam("entityTypeId") entityTypeId: Int): Response {
        return try {
            val state = bridgeClient.getSmartProcessState(entityTypeId)
            Response.ok(ApiResponse.ok(state)).build()
        } catch (e: Exception) {
            log.errorf("Failed to get smart process state for entityTypeId=%d: %s", entityTypeId, e.message)
            Response.status(Response.Status.SERVICE_UNAVAILABLE)
                .entity(ApiResponse.error<ProcessStateDto>("Failed to load process state: ${e.message}"))
                .build()
        }
    }

    /**
     * POST /smart/{entityTypeId}/items
     * Creates a new item in a Smart Process.
     * Body: {"title": "...", "stage_id": "...", "assigned_by_id": 1}
     */
    @POST
    @Path("/{entityTypeId}/items")
    fun addItem(
        @PathParam("entityTypeId") entityTypeId: Int,
        body: Map<String, Any>
    ): Response {
        val title = body["title"] as? String
        if (title.isNullOrBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                .entity(ApiResponse.error<SmartItemDto>("'title' is required"))
                .build()
        }
        return try {
            val item = bridgeClient.addSmartItem(entityTypeId, body)
            Response.status(Response.Status.CREATED).entity(ApiResponse.ok(item)).build()
        } catch (e: Exception) {
            log.errorf("Failed to add smart item: %s", e.message)
            Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity(ApiResponse.error<SmartItemDto>("Failed to create item: ${e.message}"))
                .build()
        }
    }

    /**
     * POST /smart/{entityTypeId}/items/{itemId}/move?stage_id={stageId}
     * Moves an item to a different pipeline stage.
     */
    @POST
    @Path("/{entityTypeId}/items/{itemId}/move")
    fun moveItem(
        @PathParam("entityTypeId") entityTypeId: Int,
        @PathParam("itemId") itemId: Int,
        @QueryParam("stage_id") stageId: String
    ): Response {
        if (stageId.isBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                .entity(ApiResponse.error<Boolean>("stage_id is required"))
                .build()
        }
        return try {
            val result = bridgeClient.moveSmartItem(entityTypeId, itemId, stageId)
            Response.ok(result).build()
        } catch (e: Exception) {
            log.errorf("Failed to move item %d: %s", itemId, e.message)
            Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity(ApiResponse.error<Boolean>("Failed to move item: ${e.message}"))
                .build()
        }
    }
}
