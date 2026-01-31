import {
  DocumentCheckIcon,
  EyeIcon,
  ClipboardDocumentCheckIcon,
  UserGroupIcon,
  SparklesIcon,
  ClockIcon,
  ShieldCheckIcon,
  BuildingOffice2Icon,
  UsersIcon,
  LightBulbIcon,
  StarIcon,
  ArchiveBoxIcon,
  DocumentDuplicateIcon,
  FireIcon,
  NewspaperIcon,
  EnvelopeOpenIcon,
  PuzzlePieceIcon,
  CheckBadgeIcon,
  RocketLaunchIcon,
  FlagIcon,
  DocumentArrowDownIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';

export const sectionIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  final_verdict: DocumentCheckIcon,
  between_the_lines: EyeIcon,
  scorecard_health: ClipboardDocumentCheckIcon,
  scorecard_role_fit: UserGroupIcon,
  scorecard_personal: SparklesIcon,
  hours_estimate: ClockIcon,
  gate_check: ShieldCheckIcon,
  company_research: BuildingOffice2Icon,
  leadership_research: UsersIcon,
  strategy_research: LightBulbIcon,
  glassdoor_research: StarIcon,
  evidence_cleanup: ArchiveBoxIcon,
  raw_jd: DocumentDuplicateIcon,
  cl_pep_talk: FireIcon,
  cl_resume_headlines: NewspaperIcon,
  cl_intro: EnvelopeOpenIcon,
  cl_problem: PuzzlePieceIcon,
  cl_proof: CheckBadgeIcon,
  cl_why_now: RocketLaunchIcon,
  cl_closing: FlagIcon,
  cl_assembled: DocumentArrowDownIcon,
};

// Default icon for unknown sections
export const DefaultSectionIcon = DocumentTextIcon;

export const getSectionIcon = (sectionType: string): React.ComponentType<{ className?: string }> => {
  return sectionIcons[sectionType] || DefaultSectionIcon;
};
