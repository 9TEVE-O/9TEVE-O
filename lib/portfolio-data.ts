import experience from "@/data/experience.json";
import profile from "@/data/profile.json";
import projects from "@/data/projects.json";
import skills from "@/data/skills.json";

export type PortfolioLink = {
  label: string;
  url: string;
};

export type PortfolioProject = {
  id: string;
  name: string;
  problem: string;
  role: string;
  techStack: string[];
  metrics: string[];
  links: PortfolioLink[];
  evidence: string[];
};

export type PortfolioSkill = {
  name: string;
  category: string;
  evidenceProjectIds: string[];
};

export type PortfolioProfile = {
  name: string;
  title: string;
  location: string;
  summary: string;
  positioning: string;
  contact: {
    email: string;
    linkedin: string;
    github: string;
    website: string;
  };
};

export type PortfolioExperience = {
  id: string;
  role: string;
  organization: string;
  period: string;
  summary: string;
  projectIds: string[];
};

export type PortfolioData = {
  profile: PortfolioProfile;
  projects: PortfolioProject[];
  skills: PortfolioSkill[];
  experience: PortfolioExperience[];
};

const portfolioData: PortfolioData = {
  profile: profile as PortfolioProfile,
  projects: projects as PortfolioProject[],
  skills: skills as PortfolioSkill[],
  experience: experience as PortfolioExperience[],
};

const cachedEvidenceText = JSON.stringify(portfolioData, null, 2);

export function getPortfolioData(): PortfolioData {
  return portfolioData;
}

export function getEvidenceText(): string {
  return cachedEvidenceText;
}
