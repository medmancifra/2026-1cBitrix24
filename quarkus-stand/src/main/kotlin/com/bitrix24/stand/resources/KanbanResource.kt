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
 * Kanban Resource — Visual screen for Kanban board management.
 *
 * Implements Phase 2 requirement:
 * "Generate visual screens — creation, connection to operational
 *  business process chains, pause/stop, delete"
 *
 * Endpoints:
 * GET  /kanban/{entityType}/board       — Full board state (all stages + cards)
 * POST /kanban/{entityType}/cards/{id}/move — Move card to stage
 */
@Path("/kanban")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
@ApplicationScoped
class KanbanResource {

    private val log: Logger = Logger.getLogger(KanbanResource::class.java)

    @Inject
    @RestClient
    lateinit var bridgeClient: Bitrix24BridgeClient

    /**
     * GET /kanban/{entityType}/board
     * Returns full Kanban board state: all stages with their task cards.
     * entityType: 1 = My Tasks, 2 = Group Tasks
     */
    @GET
    @Path("/{entityType}/board")
    fun getBoard(@PathParam("entityType") entityType: Int): Response {
        return try {
            val board = bridgeClient.getKanbanBoard(entityType)
            Response.ok(ApiResponse.ok(board)).build()
        } catch (e: Exception) {
            log.errorf("Failed to get Kanban board for entityType=%d: %s", entityType, e.message)
            Response.status(Response.Status.SERVICE_UNAVAILABLE)
                .entity(ApiResponse.error<KanbanBoardDto>("Failed to load board: ${e.message}"))
                .build()
        }
    }

    /**
     * POST /kanban/{entityType}/cards/{taskId}/move?stage_id={stageId}
     * Moves a Kanban card (task) to a different stage.
     */
    @POST
    @Path("/{entityType}/cards/{taskId}/move")
    fun moveCard(
        @PathParam("entityType") entityType: Int,
        @PathParam("taskId") taskId: Int,
        @QueryParam("stage_id") stageId: Int
    ): Response {
        if (stageId <= 0) {
            return Response.status(Response.Status.BAD_REQUEST)
                .entity(ApiResponse.error<Boolean>("stage_id must be a positive integer"))
                .build()
        }
        return try {
            val result = bridgeClient.moveKanbanCard(entityType, taskId, stageId)
            Response.ok(result).build()
        } catch (e: Exception) {
            log.errorf("Failed to move card %d to stage %d: %s", taskId, stageId, e.message)
            Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity(ApiResponse.error<Boolean>("Failed to move card: ${e.message}"))
                .build()
        }
    }
}
