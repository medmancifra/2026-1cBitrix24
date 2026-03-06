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
import java.time.Instant

/**
 * Vitrine Resource — Visual showcase panel for Bitrix24 bundles.
 *
 * Implements Phase 2 requirement:
 * "Generate visual screens for functionality testing:
 *  - Showcase and liveness statuses of bundles (mini-app)"
 *
 * Endpoints:
 * GET  /vitrine              — Full vitrine state (all bundles)
 * GET  /vitrine/bundles      — List of all registered bundles with status
 * GET  /vitrine/bundles/{name} — Status of a specific bundle
 */
@Path("/vitrine")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
@ApplicationScoped
class VitrineResource {

    private val log: Logger = Logger.getLogger(VitrineResource::class.java)

    @Inject
    @RestClient
    lateinit var bridgeClient: Bitrix24BridgeClient

    /**
     * GET /vitrine
     * Returns the full vitrine panel state with all bundle statuses.
     * This is the main visual dashboard screen.
     */
    @GET
    fun getVitrineState(): Response {
        return try {
            val statuses = bridgeClient.getAllBundleStatuses()
            val state = VitrineState(bundles = statuses)
            Response.ok(ApiResponse.ok(state)).build()
        } catch (e: Exception) {
            log.errorf("Failed to get vitrine state: %s", e.message)
            Response.status(Response.Status.SERVICE_UNAVAILABLE)
                .entity(ApiResponse.error<VitrineState>("Bridge service unavailable: ${e.message}"))
                .build()
        }
    }

    /**
     * GET /vitrine/bundles
     * Returns list of all registered bundles with their liveness status.
     */
    @GET
    @Path("/bundles")
    fun listBundles(): Response {
        return try {
            val statuses = bridgeClient.getAllBundleStatuses()
            Response.ok(ApiResponse.ok(statuses)).build()
        } catch (e: Exception) {
            log.errorf("Failed to list bundles: %s", e.message)
            // Return mock data if bridge is unavailable (dev mode)
            val mockStatuses = getMockBundleStatuses()
            Response.ok(ApiResponse.ok(mockStatuses, "Using mock data - bridge unavailable")).build()
        }
    }

    /**
     * GET /vitrine/bundles/{name}
     * Returns detailed status of a specific bundle by name.
     */
    @GET
    @Path("/bundles/{name}")
    fun getBundleStatus(@PathParam("name") name: String): Response {
        return try {
            val statuses = bridgeClient.getAllBundleStatuses()
            val bundle = statuses.find { it.bundle == name }
                ?: return Response.status(Response.Status.NOT_FOUND)
                    .entity(ApiResponse.error<BundleStatus>("Bundle '$name' not found"))
                    .build()
            Response.ok(ApiResponse.ok(bundle)).build()
        } catch (e: Exception) {
            log.errorf("Failed to get bundle status for '%s': %s", name, e.message)
            Response.status(Response.Status.SERVICE_UNAVAILABLE)
                .entity(ApiResponse.error<BundleStatus>("Bridge service unavailable"))
                .build()
        }
    }

    /**
     * Returns mock bundle statuses for development/testing when bridge is unavailable.
     */
    private fun getMockBundleStatuses(): List<BundleStatus> {
        val now = Instant.now().toString()
        return listOf(
            BundleStatus(
                bundle = "kanban",
                status = "healthy",
                metrics = mapOf("stage_count" to 5, "card_count" to 23),
                checkedAt = now
            ),
            BundleStatus(
                bundle = "smart_processes",
                status = "healthy",
                metrics = mapOf("type_count" to 3, "item_count" to 47),
                checkedAt = now
            )
        )
    }
}
