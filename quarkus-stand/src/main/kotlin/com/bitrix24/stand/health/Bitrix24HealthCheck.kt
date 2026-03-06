package com.bitrix24.stand.health

import com.bitrix24.stand.services.Bitrix24BridgeClient
import jakarta.enterprise.context.ApplicationScoped
import jakarta.inject.Inject
import org.eclipse.microprofile.health.HealthCheck
import org.eclipse.microprofile.health.HealthCheckResponse
import org.eclipse.microprofile.health.Readiness
import org.eclipse.microprofile.rest.client.inject.RestClient

/**
 * Readiness health check — verifies connectivity to the Bitrix24 Python bridge.
 *
 * Exposed at: GET /health/ready
 * Used by Phase 3 testing to verify end-to-end connectivity.
 */
@Readiness
@ApplicationScoped
class Bitrix24BridgeHealthCheck : HealthCheck {

    @Inject
    @RestClient
    lateinit var bridgeClient: Bitrix24BridgeClient

    override fun call(): HealthCheckResponse {
        return try {
            bridgeClient.getHealth()
            HealthCheckResponse.builder()
                .name("bitrix24-bridge")
                .up()
                .withData("bridge", "reachable")
                .build()
        } catch (e: Exception) {
            HealthCheckResponse.builder()
                .name("bitrix24-bridge")
                .down()
                .withData("error", e.message ?: "unknown")
                .build()
        }
    }
}
