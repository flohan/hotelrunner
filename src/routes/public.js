import { Router } from "express";
import { z } from "zod";
import { isIsoDate } from "../utils/date.js";
import { searchAvailability } from "../services/hotelrunnerClient.js";

export const publicRouter = Router();

const AvailabilitySchema = z.object({
  check_in: z.string().refine(isIsoDate, "check_in must be YYYY-MM-DD"),
  check_out: z.string().refine(isIsoDate, "check_out must be YYYY-MM-DD"),
  adults: z.number().int().positive().max(10),
  children: z.number().int().min(0).max(10).default(0),
  currency: z.string().default("EUR"),
});

publicRouter.post("/hotelrunner/public/availability", async (req, res, next) => {
  try {
    const body = AvailabilitySchema.parse(req.body);
    const data = await searchAvailability(body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

// Backwards-compatible alias for Retell flows:
publicRouter.post("/retell/public/check_availability", async (req, res, next) => {
  try {
    const body = AvailabilitySchema.parse(req.body);
    const data = await searchAvailability(body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});
