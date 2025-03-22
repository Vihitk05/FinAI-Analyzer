import { FileText } from "lucide-react";
import { Button } from "@/components/ui/button";

export function RecentDocuments() {
  const documents = [
    {
      id: 1,
      name: "Amazon Financial Report 2023",
      date: "Mar 15, 2023",
      type: "Annual Report",
    },
    {
      id: 2,
      name: "Tesla Q2 Financial Statement",
      date: "Jul 22, 2023",
      type: "Quarterly Report",
    },
    {
      id: 3,
      name: "Microsoft Annual Report",
      date: "Oct 10, 2023",
      type: "Annual Report",
    },
  ];

  return (
    <div className="space-y-4">
      {documents.map((doc) => (
        <div key={doc.id} className="flex items-center justify-between p-2 rounded-md hover:bg-muted">
          <div className="flex items-center">
            <FileText className="h-5 w-5 text-muted-foreground mr-2" />
            <div>
              <p className="text-sm font-medium">{doc.name}</p>
              <p className="text-xs text-muted-foreground">
                {doc.date} • {doc.type}
              </p>
            </div>
          </div>
          <Button variant="ghost" size="sm">
            View
          </Button>
        </div>
      ))}
    </div>
  );
}