/**
 * OpenAPI/Swagger setup (static definition for now).
 */
export const swaggerDefinition = {
  openapi: "3.0.3",
  info: {
    title: "Retell Agent Optimized API",
    version: "1.0.0",
    description: "Public and tool endpoints for Retell + HotelRunner integration"
  },
  servers: [{ url: "/" }],
  paths: {
    "/healthz": {
      get: {
        summary: "Health check",
        responses: { "200": { description: "OK" } }
      }
    },
    "/hotelrunner/public/availability": {
      post: {
        summary: "Search availability (HotelRunner)",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: {
                  check_in: { type: "string", example: "2025-10-01" },
                  check_out: { type: "string", example: "2025-10-11" },
                  adults: { type: "integer", example: 2 },
                  children: { type: "integer", example: 0 },
                  currency: { type: "string", example: "EUR" }
                },
                required: ["check_in","check_out","adults"]
              }
            }
          }
        },
        responses: {
          "200": { description: "Availability result from HotelRunner" },
          "400": { description: "Validation error" },
          "503": { description: "Upstream/circuit temporarily unavailable" }
        }
      }
    },
    "/retell/public/check_availability": {
      post: {
        summary: "Compatibility alias for availability search",
        requestBody: { $ref: "#/paths/~1hotelrunner~1public~1availability/post/requestBody" },
        responses: { $ref: "#/paths/~1hotelrunner~1public~1availability/post/responses" }
      }
    },
    "/retell/tool/ping": {
      get: {
        summary: "Internal tool ping (requires x-tool-secret)",
        responses: {
          "200": { description: "OK" },
          "401": { description: "Unauthorized" }
        }
      }
    }
  }
};
