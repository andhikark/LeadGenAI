"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Scraper } from "@/components/scraper"
import { DataEnhancement } from "@/components/data-enhancement"
import { Header } from "@/components/header"
import { Sidebar } from "@/components/sidebar"

export function Dashboard() {
  const [activeTab, setActiveTab] = useState("scraper")

  return (
    <div className="min-h-screen bg-mint-50">
      <Header />
      <div className="flex">
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        <main className="flex-1 p-6">
          <Tabs defaultValue="scraper" value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full max-w-md grid-cols-2 mb-8">
              <TabsTrigger value="scraper">Scraper</TabsTrigger>
              <TabsTrigger value="enhancement">Data Enhancement</TabsTrigger>
            </TabsList>
            <TabsContent value="scraper">
              <Scraper />
            </TabsContent>
            <TabsContent value="enhancement">
              <DataEnhancement />
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </div>
  )
}
