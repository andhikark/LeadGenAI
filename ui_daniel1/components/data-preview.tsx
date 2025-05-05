"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Search, Filter } from "lucide-react"

// Mock data for demonstration
const mockData = [
  {
    id: 1,
    company: "Acme Inc",
    website: "acme.com",
    industry: "Software",
    employees: "50-200",
    revenue: "$10M-$50M",
    contact: "John Smith",
    email: "john@acme.com",
  },
  {
    id: 2,
    company: "TechCorp",
    website: "techcorp.io",
    industry: "SaaS",
    employees: "10-50",
    revenue: "$1M-$10M",
    contact: "Sarah Johnson",
    email: "sarah@techcorp.io",
  },
  {
    id: 3,
    company: "DataSystems",
    website: "datasystems.co",
    industry: "Data Analytics",
    employees: "200-500",
    revenue: "$50M-$100M",
    contact: "Michael Chen",
    email: "michael@datasystems.co",
  },
  {
    id: 4,
    company: "CloudWorks",
    website: "cloudworks.net",
    industry: "Cloud Services",
    employees: "50-200",
    revenue: "$10M-$50M",
    contact: "Emily Davis",
    email: "emily@cloudworks.net",
  },
  {
    id: 5,
    company: "AI Solutions",
    website: "aisolutions.ai",
    industry: "Artificial Intelligence",
    employees: "10-50",
    revenue: "$1M-$10M",
    contact: "David Wilson",
    email: "david@aisolutions.ai",
  },
]

export function DataPreview() {
  const [selectedRows, setSelectedRows] = useState<number[]>(mockData.map((row) => row.id))
  const [searchTerm, setSearchTerm] = useState("")

  const toggleSelectAll = () => {
    if (selectedRows.length === mockData.length) {
      setSelectedRows([])
    } else {
      setSelectedRows(mockData.map((row) => row.id))
    }
  }

  const toggleSelectRow = (id: number) => {
    if (selectedRows.includes(id)) {
      setSelectedRows(selectedRows.filter((rowId) => rowId !== id))
    } else {
      setSelectedRows([...selectedRows, id])
    }
  }

  const filteredData = mockData.filter(
    (row) =>
      row.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
      row.industry.toLowerCase().includes(searchTerm.toLowerCase()) ||
      row.contact.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Preview and Select Data</h3>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search data..."
              className="w-64 pl-8"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <Button variant="outline" size="icon">
            <Filter className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">
                <Checkbox
                  checked={selectedRows.length === mockData.length && mockData.length > 0}
                  onCheckedChange={toggleSelectAll}
                />
              </TableHead>
              <TableHead>Company</TableHead>
              <TableHead>Website</TableHead>
              <TableHead>Industry</TableHead>
              <TableHead>Employees</TableHead>
              <TableHead>Revenue</TableHead>
              <TableHead>Contact</TableHead>
              <TableHead>Email</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredData.map((row) => (
              <TableRow key={row.id}>
                <TableCell>
                  <Checkbox checked={selectedRows.includes(row.id)} onCheckedChange={() => toggleSelectRow(row.id)} />
                </TableCell>
                <TableCell>{row.company}</TableCell>
                <TableCell>{row.website}</TableCell>
                <TableCell>{row.industry}</TableCell>
                <TableCell>{row.employees}</TableCell>
                <TableCell>{row.revenue}</TableCell>
                <TableCell>{row.contact}</TableCell>
                <TableCell>{row.email}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {selectedRows.length} of {mockData.length} rows selected for enrichment
        </div>
        <Button
          variant="outline"
          onClick={() => setSelectedRows(mockData.map((row) => row.id))}
          disabled={selectedRows.length === mockData.length}
        >
          Select All
        </Button>
      </div>
    </div>
  )
}
