import { describe, expect, it } from "vitest";
import { STATUS_COLOR, statusToColor, statusToLabel, worseStatus, worstStatus } from "./statusColor";

describe("statusToColor", () => {
  it("returns a distinct color for each status", () => {
    const colors = new Set(["up", "warn", "down"].map((s) => statusToColor(s as never)));
    expect(colors.size).toBe(3);
  });

  it("matches the STATUS_COLOR table", () => {
    expect(statusToColor("up")).toBe(STATUS_COLOR.up);
    expect(statusToColor("warn")).toBe(STATUS_COLOR.warn);
    expect(statusToColor("down")).toBe(STATUS_COLOR.down);
  });
});

describe("statusToLabel", () => {
  it("gives a human-readable label for every status", () => {
    expect(statusToLabel("up")).toBe("Up");
    expect(statusToLabel("warn")).toBe("Degraded");
    expect(statusToLabel("down")).toBe("Down");
  });
});

describe("worseStatus", () => {
  it("down beats warn and up", () => {
    expect(worseStatus("down", "up")).toBe("down");
    expect(worseStatus("up", "down")).toBe("down");
    expect(worseStatus("down", "warn")).toBe("down");
  });

  it("warn beats up", () => {
    expect(worseStatus("up", "warn")).toBe("warn");
    expect(worseStatus("warn", "up")).toBe("warn");
  });

  it("is idempotent for equal statuses", () => {
    expect(worseStatus("warn", "warn")).toBe("warn");
  });
});

describe("worstStatus", () => {
  it("returns up for an empty list", () => {
    expect(worstStatus([])).toBe("up");
  });

  it("finds the single worst status in a mixed list", () => {
    expect(worstStatus(["up", "up", "warn", "up"])).toBe("warn");
    expect(worstStatus(["up", "warn", "down", "warn"])).toBe("down");
  });

  it("stays up when everything is up", () => {
    expect(worstStatus(["up", "up", "up"])).toBe("up");
  });
});
