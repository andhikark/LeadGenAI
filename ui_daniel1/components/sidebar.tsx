"use client"

import { Database, LineChart, Search, Users } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface SidebarProps {
  activeTab: string
  setActiveTab: (tab: string) => void
}

export function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  return (
    <div className="hidden lg:block w-64 border-r bg-white">
      <div className="flex flex-col gap-2 p-4">
        <Button
          variant="ghost"
          className={cn("justify-start gap-2", activeTab === "scraper" && "bg-mint-100 text-teal-700")}
          onClick={() => setActiveTab("scraper")}
        >
          <Search className="h-5 w-5" />
          Scraper
        </Button>
        <Button
          variant="ghost"
          className={cn("justify-start gap-2", activeTab === "enhancement" && "bg-mint-100 text-teal-700")}
          onClick={() => setActiveTab("enhancement")}
        >
          <Database className="h-5 w-5" />
          Data Enhancement
        </Button>
        <Button variant="ghost" className="justify-start gap-2">
          <Users className="h-5 w-5" />
          Leads
        </Button>
        <Button variant="ghost" className="justify-start gap-2">
          <LineChart className="h-5 w-5" />
          Analytics
        </Button>
      </div>
    </div>
  )
}
