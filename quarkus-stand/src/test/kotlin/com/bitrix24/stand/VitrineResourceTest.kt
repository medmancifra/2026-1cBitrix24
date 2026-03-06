package com.bitrix24.stand

import io.quarkus.test.junit.QuarkusTest
import io.restassured.module.kotlin.extensions.Then
import io.restassured.module.kotlin.extensions.When
import org.hamcrest.CoreMatchers.notNullValue
import org.junit.jupiter.api.Test

@QuarkusTest
class VitrineResourceTest {

    @Test
    fun `GET vitrine bundles returns list (mock or real)`() {
        When {
            get("/vitrine/bundles")
        } Then {
            // Should return 200 even when bridge is unavailable (mock fallback)
            statusCode(200)
            body("success", notNullValue())
        }
    }
}
