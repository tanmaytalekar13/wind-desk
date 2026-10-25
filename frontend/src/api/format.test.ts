import { expect, test } from "vitest";
import { fmtMW, fmtPct } from "./format";

test("fmtMW", () => { expect(fmtMW(1234.4)).toBe("1,234 MW"); expect(fmtMW(null)).toBe("–"); });
test("fmtPct", () => { expect(fmtPct(12.345)).toBe("12.3%"); });
