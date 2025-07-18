import { FaTiktok } from "react-icons/fa";
import { Instagram, Facebook, Twitter, Linkedin } from "lucide-react"; // adjust to your actual imports

export const socialPlatforms = [
   {
    id: "Instagram",
    name: "instagram",
    icon: Instagram,
    color: "bg-gradient-to-br from-purple-600 to-pink-500",
  },
  {
    id: "Facebook",
    name: "facebook",
    icon: Facebook,
    color: "bg-blue-600",
  },
  {
    id: "Twitter",
    name: "twitter",
    icon: Twitter,
    color: "bg-sky-500",
  },
  {
    id: "Linkedin",
    name: "linkedIn",
    icon: Linkedin,
    color: "bg-blue-700",

  },
  {
    id: "TikTok",
    name: "tiktok",
    icon: FaTiktok,
    color: "bg-black"

  },
];
