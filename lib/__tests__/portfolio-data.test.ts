import { describe, it, expect } from "vitest";
import {
  getPortfolioData,
  getEvidenceText,
  type PortfolioData,
  type PortfolioProfile,
  type PortfolioProject,
  type PortfolioSkill,
  type PortfolioExperience,
  type PortfolioLink,
} from "../portfolio-data";

describe("getPortfolioData", () => {
  describe("return shape", () => {
    it("returns an object with profile, projects, skills, and experience keys", () => {
      const data = getPortfolioData();

      expect(data).toHaveProperty("profile");
      expect(data).toHaveProperty("projects");
      expect(data).toHaveProperty("skills");
      expect(data).toHaveProperty("experience");
    });

    it("returns exactly four top-level keys", () => {
      const data = getPortfolioData();
      expect(Object.keys(data).sort()).toEqual(
        ["experience", "profile", "projects", "skills"].sort(),
      );
    });
  });

  describe("profile", () => {
    it("is an object (not an array)", () => {
      const { profile } = getPortfolioData();
      expect(typeof profile).toBe("object");
      expect(Array.isArray(profile)).toBe(false);
    });

    it("has a non-empty name field", () => {
      const { profile } = getPortfolioData();
      expect(typeof profile.name).toBe("string");
      expect(profile.name.length).toBeGreaterThan(0);
    });

    it("has a title field", () => {
      const { profile } = getPortfolioData();
      expect(typeof profile.title).toBe("string");
    });

    it("has a location field", () => {
      const { profile } = getPortfolioData();
      expect(typeof profile.location).toBe("string");
    });

    it("has a summary field", () => {
      const { profile } = getPortfolioData();
      expect(typeof profile.summary).toBe("string");
    });

    it("has a positioning field", () => {
      const { profile } = getPortfolioData();
      expect(typeof profile.positioning).toBe("string");
    });

    it("has a contact object with email, linkedin, github, and website fields", () => {
      const { profile } = getPortfolioData();
      expect(profile.contact).toBeDefined();
      expect(typeof profile.contact).toBe("object");
      expect("email" in profile.contact).toBe(true);
      expect("linkedin" in profile.contact).toBe(true);
      expect("github" in profile.contact).toBe(true);
      expect("website" in profile.contact).toBe(true);
    });

    it("returns the same profile object on repeated calls", () => {
      const first = getPortfolioData().profile;
      const second = getPortfolioData().profile;
      expect(first).toEqual(second);
    });
  });

  describe("projects", () => {
    it("is an array", () => {
      const { projects } = getPortfolioData();
      expect(Array.isArray(projects)).toBe(true);
    });

    it("has at least one project", () => {
      const { projects } = getPortfolioData();
      expect(projects.length).toBeGreaterThan(0);
    });

    it("each project has required string fields: id, name, problem, role", () => {
      const { projects } = getPortfolioData();
      for (const project of projects) {
        expect(typeof project.id).toBe("string");
        expect(project.id.length).toBeGreaterThan(0);
        expect(typeof project.name).toBe("string");
        expect(typeof project.problem).toBe("string");
        expect(typeof project.role).toBe("string");
      }
    });

    it("each project has techStack as a string array", () => {
      const { projects } = getPortfolioData();
      for (const project of projects) {
        expect(Array.isArray(project.techStack)).toBe(true);
        for (const tech of project.techStack) {
          expect(typeof tech).toBe("string");
        }
      }
    });

    it("each project has metrics as an array", () => {
      const { projects } = getPortfolioData();
      for (const project of projects) {
        expect(Array.isArray(project.metrics)).toBe(true);
      }
    });

    it("each project has links as an array with label and url fields", () => {
      const { projects } = getPortfolioData();
      for (const project of projects) {
        expect(Array.isArray(project.links)).toBe(true);
        for (const link of project.links) {
          expect(typeof link.label).toBe("string");
          expect(typeof link.url).toBe("string");
        }
      }
    });

    it("each project has evidence as a string array", () => {
      const { projects } = getPortfolioData();
      for (const project of projects) {
        expect(Array.isArray(project.evidence)).toBe(true);
        for (const ev of project.evidence) {
          expect(typeof ev).toBe("string");
        }
      }
    });

    it("project ids are unique", () => {
      const { projects } = getPortfolioData();
      const ids = projects.map((p) => p.id);
      expect(new Set(ids).size).toBe(ids.length);
    });
  });

  describe("skills", () => {
    it("is an array", () => {
      const { skills } = getPortfolioData();
      expect(Array.isArray(skills)).toBe(true);
    });

    it("has at least one skill", () => {
      const { skills } = getPortfolioData();
      expect(skills.length).toBeGreaterThan(0);
    });

    it("each skill has name, category, and evidenceProjectIds fields", () => {
      const { skills } = getPortfolioData();
      for (const skill of skills) {
        expect(typeof skill.name).toBe("string");
        expect(skill.name.length).toBeGreaterThan(0);
        expect(typeof skill.category).toBe("string");
        expect(Array.isArray(skill.evidenceProjectIds)).toBe(true);
      }
    });

    it("evidenceProjectIds contains strings", () => {
      const { skills } = getPortfolioData();
      for (const skill of skills) {
        for (const id of skill.evidenceProjectIds) {
          expect(typeof id).toBe("string");
        }
      }
    });
  });

  describe("experience", () => {
    it("is an array", () => {
      const { experience } = getPortfolioData();
      expect(Array.isArray(experience)).toBe(true);
    });

    it("has at least one experience entry", () => {
      const { experience } = getPortfolioData();
      expect(experience.length).toBeGreaterThan(0);
    });

    it("each entry has required string fields: id, role, organization, period, summary", () => {
      const { experience } = getPortfolioData();
      for (const entry of experience) {
        expect(typeof entry.id).toBe("string");
        expect(entry.id.length).toBeGreaterThan(0);
        expect(typeof entry.role).toBe("string");
        expect(typeof entry.organization).toBe("string");
        expect(typeof entry.period).toBe("string");
        expect(typeof entry.summary).toBe("string");
      }
    });

    it("each entry has projectIds as a string array", () => {
      const { experience } = getPortfolioData();
      for (const entry of experience) {
        expect(Array.isArray(entry.projectIds)).toBe(true);
        for (const id of entry.projectIds) {
          expect(typeof id).toBe("string");
        }
      }
    });

    it("experience ids are unique", () => {
      const { experience } = getPortfolioData();
      const ids = experience.map((e) => e.id);
      expect(new Set(ids).size).toBe(ids.length);
    });
  });

  describe("referential integrity", () => {
    it("all evidenceProjectIds in skills reference valid project ids", () => {
      const { skills, projects } = getPortfolioData();
      const projectIds = new Set(projects.map((p) => p.id));
      for (const skill of skills) {
        for (const id of skill.evidenceProjectIds) {
          expect(projectIds.has(id)).toBe(true);
        }
      }
    });

    it("all projectIds in experience reference valid project ids", () => {
      const { experience, projects } = getPortfolioData();
      const projectIds = new Set(projects.map((p) => p.id));
      for (const entry of experience) {
        for (const id of entry.projectIds) {
          expect(projectIds.has(id)).toBe(true);
        }
      }
    });
  });
});

describe("getEvidenceText", () => {
  it("returns a non-empty string", () => {
    const text = getEvidenceText();
    expect(typeof text).toBe("string");
    expect(text.length).toBeGreaterThan(0);
  });

  it("returns valid JSON", () => {
    const text = getEvidenceText();
    expect(() => JSON.parse(text)).not.toThrow();
  });

  it("parses back to the same structure as getPortfolioData()", () => {
    const data = getPortfolioData();
    const parsed = JSON.parse(getEvidenceText()) as PortfolioData;

    expect(parsed).toEqual(data);
  });

  it("uses 2-space indentation (pretty-printed)", () => {
    const text = getEvidenceText();
    // A pretty-printed JSON object with 2-space indent starts its first key with two spaces
    expect(text).toMatch(/^\{\n {2}"/);
  });

  it("contains the profile key at the top level", () => {
    const text = getEvidenceText();
    const parsed = JSON.parse(text);
    expect(parsed).toHaveProperty("profile");
  });

  it("contains the projects key at the top level", () => {
    const text = getEvidenceText();
    const parsed = JSON.parse(text);
    expect(parsed).toHaveProperty("projects");
  });

  it("contains the skills key at the top level", () => {
    const text = getEvidenceText();
    const parsed = JSON.parse(text);
    expect(parsed).toHaveProperty("skills");
  });

  it("contains the experience key at the top level", () => {
    const text = getEvidenceText();
    const parsed = JSON.parse(text);
    expect(parsed).toHaveProperty("experience");
  });

  it("produces consistent output across multiple calls", () => {
    expect(getEvidenceText()).toBe(getEvidenceText());
  });
});