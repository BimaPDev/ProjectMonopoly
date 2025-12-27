"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "@/hooks/use-toast";
import { useGroup } from "@/components/groupContext";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Loader2,
  Target,
  Users,
  Layers,
  Upload,
  Calendar,
  Sparkles,
  FileText,
  BarChart3,
} from "lucide-react";

// Types
interface AudienceArchetype {
  id: string;
  name: string;
  description: string;
  demographics: Record<string, unknown>;
}

interface CadenceConfig {
  platforms: string[];
  posts_per_week: number;
  preferred_days: string[];
  time_windows: string[];
}

interface WizardOptions {
  goals: string[];
  audiences: AudienceArchetype[];
  pillars: string[];
  platforms: string[];
}

interface Campaign {
  id: string;
  name: string;
  goal: string;
  status: string;
  created_at: string;
}

interface Draft {
  id: string;
  platform: string;
  post_type: string;
  hook: string;
  caption: string;
  hashtags: string[];
  cta: string;
  confidence: number;
  status: string;
}

// Step indicator component
function StepIndicator({ currentStep, steps }: { currentStep: number; steps: string[] }) {
  return (
    <div className="flex items-center justify-center mb-8">
      {steps.map((step, idx) => (
        <div key={step} className="flex items-center">
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
              idx < currentStep
                ? "bg-emerald-500 text-white"
                : idx === currentStep
                ? "bg-violet-600 text-white ring-4 ring-violet-600/30"
                : "bg-zinc-800 text-zinc-400"
            }`}
          >
            {idx < currentStep ? <Check className="w-5 h-5" /> : idx + 1}
          </div>
          {idx < steps.length - 1 && (
            <div
              className={`w-16 h-1 mx-2 rounded ${
                idx < currentStep ? "bg-emerald-500" : "bg-zinc-800"
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );
}

export default function CampaignsPage() {
  const { activeGroup } = useGroup();
  const [view, setView] = useState<"list" | "wizard" | "details">("list");
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Wizard state
  const [currentStep, setCurrentStep] = useState(0);
  const [wizardOptions, setWizardOptions] = useState<WizardOptions | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    goal: "",
    audience: null as AudienceArchetype | null,
    pillars: [] as string[],
    cadence: {
      platforms: [] as string[],
      posts_per_week: 3,
      preferred_days: ["Monday", "Wednesday", "Friday"],
      time_windows: ["evening"],
    } as CadenceConfig,
  });

  const steps = ["Goal", "Audience", "Pillars", "Assets", "Cadence"];
  const stepIcons = [Target, Users, Layers, Upload, Calendar];

  // Fetch campaigns on load
  useEffect(() => {
    if (view === "list") {
      fetchCampaigns();
    }
  }, [view]);

  // Fetch wizard options when entering wizard
  useEffect(() => {
    if (view === "wizard" && !wizardOptions) {
      fetchWizardOptions();
    }
  }, [view, wizardOptions]);

  async function fetchCampaigns() {
    setIsLoading(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/campaigns", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCampaigns(data.campaigns || []);
      }
    } catch (error) {
      console.error("Failed to fetch campaigns:", error);
    } finally {
      setIsLoading(false);
    }
  }

  async function fetchWizardOptions() {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/campaigns/wizard", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setWizardOptions(data);
      }
    } catch (error) {
      console.error("Failed to fetch wizard options:", error);
    }
  }

  async function fetchDrafts(campaignId: string) {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`/api/campaigns/${campaignId}/drafts`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDrafts(data.drafts || []);
      }
    } catch (error) {
      console.error("Failed to fetch drafts:", error);
    }
  }

  async function createCampaign() {
    if (!activeGroup) {
      toast({
        title: "No group selected",
        description: "Please select a group first",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/campaigns", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: formData.name,
          group_id: activeGroup.ID,
          goal: formData.goal,
          audience: formData.audience,
          pillars: formData.pillars,
          cadence: formData.cadence,
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to create campaign");
      }

      const data = await res.json();
      toast({
        title: "Campaign Created!",
        description: "Now generating your content drafts...",
      });

      // Generate drafts
      await generateDrafts(data.campaign.id);
      
      setView("list");
      resetWizard();
      fetchCampaigns();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create campaign",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }

  async function generateDrafts(campaignId: string) {
    try {
      const token = localStorage.getItem("token");
      await fetch(`/api/campaigns/${campaignId}/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });
    } catch (error) {
      console.error("Failed to generate drafts:", error);
    }
  }

  function resetWizard() {
    setCurrentStep(0);
    setFormData({
      name: "",
      goal: "",
      audience: null,
      pillars: [],
      cadence: {
        platforms: [],
        posts_per_week: 3,
        preferred_days: ["Monday", "Wednesday", "Friday"],
        time_windows: ["evening"],
      },
    });
  }

  function openCampaignDetails(campaign: Campaign) {
    setSelectedCampaign(campaign);
    fetchDrafts(campaign.id);
    setView("details");
  }

  // Validation for each step
  function canProceed(): boolean {
    switch (currentStep) {
      case 0:
        return formData.name.trim() !== "" && formData.goal !== "";
      case 1:
        return formData.audience !== null;
      case 2:
        return formData.pillars.length >= 1 && formData.pillars.length <= 5;
      case 3:
        return true; // Assets are optional
      case 4:
        return formData.cadence.platforms.length > 0;
      default:
        return false;
    }
  }

  // Render based on view
  if (view === "list") {
    return (
      <div className="min-h-screen bg-black p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Campaigns</h1>
              <p className="text-zinc-400">Manage your marketing campaigns</p>
            </div>
            <Button
              onClick={() => setView("wizard")}
              className="bg-violet-600 hover:bg-violet-700"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              New Campaign
            </Button>
          </div>

          {isLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
            </div>
          ) : campaigns.length === 0 ? (
            <Card className="bg-zinc-900 border-zinc-800">
              <CardContent className="py-12 text-center">
                <Sparkles className="w-12 h-12 mx-auto text-zinc-600 mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">
                  No campaigns yet
                </h3>
                <p className="text-zinc-400 mb-6">
                  Create your first campaign to get AI-generated content drafts
                </p>
                <Button
                  onClick={() => setView("wizard")}
                  className="bg-violet-600 hover:bg-violet-700"
                >
                  Create Campaign
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {campaigns.map((campaign) => (
                <Card
                  key={campaign.id}
                  className="bg-zinc-900 border-zinc-800 hover:border-violet-600/50 cursor-pointer transition-all"
                  onClick={() => openCampaignDetails(campaign)}
                >
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <CardTitle className="text-white">{campaign.name}</CardTitle>
                      <Badge
                        variant={campaign.status === "active" ? "default" : "secondary"}
                        className={
                          campaign.status === "active"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : ""
                        }
                      >
                        {campaign.status}
                      </Badge>
                    </div>
                    <CardDescription className="text-zinc-400">
                      Goal: {campaign.goal}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4 text-sm text-zinc-500">
                      <div className="flex items-center gap-1">
                        <FileText className="w-4 h-4" />
                        View Drafts
                      </div>
                      <div className="flex items-center gap-1">
                        <BarChart3 className="w-4 h-4" />
                        Insights
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (view === "details" && selectedCampaign) {
    return (
      <div className="min-h-screen bg-black p-8">
        <div className="max-w-6xl mx-auto">
          <Button
            variant="ghost"
            onClick={() => setView("list")}
            className="text-zinc-400 mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Campaigns
          </Button>

          <div className="flex justify-between items-start mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                {selectedCampaign.name}
              </h1>
              <div className="flex items-center gap-3">
                <Badge className="bg-violet-500/20 text-violet-400">
                  {selectedCampaign.goal}
                </Badge>
                <Badge
                  variant={selectedCampaign.status === "active" ? "default" : "secondary"}
                  className={
                    selectedCampaign.status === "active"
                      ? "bg-emerald-500/20 text-emerald-400"
                      : ""
                  }
                >
                  {selectedCampaign.status}
                </Badge>
              </div>
            </div>
            <Button
              onClick={() => generateDrafts(selectedCampaign.id).then(() => fetchDrafts(selectedCampaign.id))}
              className="bg-violet-600 hover:bg-violet-700"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Regenerate Drafts
            </Button>
          </div>

          <h2 className="text-xl font-semibold text-white mb-4">Content Drafts</h2>

          {drafts.length === 0 ? (
            <Card className="bg-zinc-900 border-zinc-800">
              <CardContent className="py-8 text-center">
                <p className="text-zinc-400">No drafts generated yet</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {drafts.map((draft) => (
                <Card key={draft.id} className="bg-zinc-900 border-zinc-800">
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <Badge className="mb-2">{draft.platform}</Badge>
                        <CardTitle className="text-white text-lg">
                          {draft.hook || "Untitled Draft"}
                        </CardTitle>
                      </div>
                      <Badge
                        variant="outline"
                        className="text-zinc-400 border-zinc-700"
                      >
                        {Math.round(draft.confidence * 100)}% confidence
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-zinc-300 mb-4">{draft.caption}</p>
                    {draft.hashtags && draft.hashtags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-4">
                        {draft.hashtags.map((tag) => (
                          <span
                            key={tag}
                            className="text-xs text-violet-400 bg-violet-500/10 px-2 py-1 rounded"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}
                    {draft.cta && (
                      <p className="text-sm text-emerald-400">CTA: {draft.cta}</p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Wizard view
  return (
    <div className="min-h-screen bg-black p-8">
      <div className="max-w-3xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => {
            setView("list");
            resetWizard();
          }}
          className="text-zinc-400 mb-6"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Cancel
        </Button>

        <h1 className="text-3xl font-bold text-white text-center mb-2">
          Campaign Wizard
        </h1>
        <p className="text-zinc-400 text-center mb-8">
          Create a structured marketing campaign in 5 easy steps
        </p>

        <StepIndicator currentStep={currentStep} steps={steps} />

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <div className="flex items-center gap-3">
              {stepIcons[currentStep] && (
                <div className="w-10 h-10 rounded-lg bg-violet-600/20 flex items-center justify-center">
                  {(() => {
                    const Icon = stepIcons[currentStep];
                    return <Icon className="w-5 h-5 text-violet-400" />;
                  })()}
                </div>
              )}
              <div>
                <CardTitle className="text-white">Step {currentStep + 1}: {steps[currentStep]}</CardTitle>
                <CardDescription className="text-zinc-400">
                  {currentStep === 0 && "Define your campaign goal"}
                  {currentStep === 1 && "Select your target audience"}
                  {currentStep === 2 && "Choose 1-5 content pillars"}
                  {currentStep === 3 && "Upload assets (optional)"}
                  {currentStep === 4 && "Set your posting cadence"}
                </CardDescription>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Step 0: Goal */}
            {currentStep === 0 && (
              <>
                <div className="space-y-2">
                  <Label className="text-white">Campaign Name</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Summer Launch Campaign"
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-white">Primary Goal</Label>
                  <div className="grid grid-cols-2 gap-3">
                    {wizardOptions?.goals.map((goal) => (
                      <button
                        key={goal}
                        onClick={() => setFormData({ ...formData, goal })}
                        className={`p-4 rounded-lg border text-left transition-all ${
                          formData.goal === goal
                            ? "border-violet-500 bg-violet-500/10"
                            : "border-zinc-700 bg-zinc-800 hover:border-zinc-600"
                        }`}
                      >
                        <span className="text-white font-medium capitalize">{goal}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Step 1: Audience */}
            {currentStep === 1 && (
              <div className="space-y-3">
                {wizardOptions?.audiences.map((audience) => (
                  <button
                    key={audience.id}
                    onClick={() => setFormData({ ...formData, audience })}
                    className={`w-full p-4 rounded-lg border text-left transition-all ${
                      formData.audience?.id === audience.id
                        ? "border-violet-500 bg-violet-500/10"
                        : "border-zinc-700 bg-zinc-800 hover:border-zinc-600"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                          formData.audience?.id === audience.id
                            ? "border-violet-500 bg-violet-500"
                            : "border-zinc-600"
                        }`}
                      >
                        {formData.audience?.id === audience.id && (
                          <Check className="w-3 h-3 text-white" />
                        )}
                      </div>
                      <div>
                        <h4 className="text-white font-medium">{audience.name}</h4>
                        <p className="text-zinc-400 text-sm">{audience.description}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {/* Step 2: Pillars */}
            {currentStep === 2 && (
              <>
                <p className="text-zinc-400 text-sm">
                  Selected: {formData.pillars.length}/5 pillars
                </p>
                <div className="grid grid-cols-2 gap-3">
                  {wizardOptions?.pillars.map((pillar) => {
                    const isSelected = formData.pillars.includes(pillar);
                    const isDisabled = !isSelected && formData.pillars.length >= 5;
                    return (
                      <button
                        key={pillar}
                        disabled={isDisabled}
                        onClick={() => {
                          if (isSelected) {
                            setFormData({
                              ...formData,
                              pillars: formData.pillars.filter((p) => p !== pillar),
                            });
                          } else {
                            setFormData({
                              ...formData,
                              pillars: [...formData.pillars, pillar],
                            });
                          }
                        }}
                        className={`p-3 rounded-lg border text-left transition-all ${
                          isSelected
                            ? "border-violet-500 bg-violet-500/10"
                            : isDisabled
                            ? "border-zinc-800 bg-zinc-900 opacity-50 cursor-not-allowed"
                            : "border-zinc-700 bg-zinc-800 hover:border-zinc-600"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <Checkbox checked={isSelected} />
                          <span className="text-white text-sm">{pillar}</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </>
            )}

            {/* Step 3: Assets (optional) */}
            {currentStep === 3 && (
              <div className="text-center py-8">
                <Upload className="w-12 h-12 mx-auto text-zinc-600 mb-4" />
                <h3 className="text-white font-medium mb-2">Upload Assets (Optional)</h3>
                <p className="text-zinc-400 text-sm mb-4">
                  You can add assets after creating the campaign
                </p>
                <Button variant="outline" className="border-zinc-700 text-zinc-400">
                  Upload Files
                </Button>
              </div>
            )}

            {/* Step 4: Cadence */}
            {currentStep === 4 && (
              <>
                <div className="space-y-4">
                  <div>
                    <Label className="text-white mb-2 block">Platforms</Label>
                    <div className="flex flex-wrap gap-2">
                      {wizardOptions?.platforms.map((platform) => {
                        const isSelected = formData.cadence.platforms.includes(platform);
                        return (
                          <button
                            key={platform}
                            onClick={() => {
                              if (isSelected) {
                                setFormData({
                                  ...formData,
                                  cadence: {
                                    ...formData.cadence,
                                    platforms: formData.cadence.platforms.filter(
                                      (p) => p !== platform
                                    ),
                                  },
                                });
                              } else {
                                setFormData({
                                  ...formData,
                                  cadence: {
                                    ...formData.cadence,
                                    platforms: [...formData.cadence.platforms, platform],
                                  },
                                });
                              }
                            }}
                            className={`px-4 py-2 rounded-lg border transition-all capitalize ${
                              isSelected
                                ? "border-violet-500 bg-violet-500/10 text-violet-400"
                                : "border-zinc-700 bg-zinc-800 text-zinc-400 hover:border-zinc-600"
                            }`}
                          >
                            {platform}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div>
                    <Label className="text-white mb-2 block">Posts per Week</Label>
                    <Select
                      value={String(formData.cadence.posts_per_week)}
                      onValueChange={(value) =>
                        setFormData({
                          ...formData,
                          cadence: {
                            ...formData.cadence,
                            posts_per_week: parseInt(value),
                          },
                        })
                      }
                    >
                      <SelectTrigger className="bg-zinc-800 border-zinc-700 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[1, 2, 3, 4, 5, 6, 7].map((n) => (
                          <SelectItem key={n} value={String(n)}>
                            {n} post{n > 1 ? "s" : ""} per week
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Navigation buttons */}
        <div className="flex justify-between mt-6">
          <Button
            variant="outline"
            onClick={() => setCurrentStep(currentStep - 1)}
            disabled={currentStep === 0}
            className="border-zinc-700 text-zinc-400"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Previous
          </Button>

          {currentStep < steps.length - 1 ? (
            <Button
              onClick={() => setCurrentStep(currentStep + 1)}
              disabled={!canProceed()}
              className="bg-violet-600 hover:bg-violet-700"
            >
              Next
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          ) : (
            <Button
              onClick={createCampaign}
              disabled={!canProceed() || isLoading}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4 mr-2" />
                  Create Campaign
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}




