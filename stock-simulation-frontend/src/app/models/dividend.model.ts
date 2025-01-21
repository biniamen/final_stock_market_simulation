// src/app/models/dividend.model.ts

export interface ListedCompany {
    id: number;
    company_name: string;
    // Add other fields as necessary
  }
  
  export interface Dividend {
    id: number;
    company: ListedCompany; // Nested object based on the Django serializer
    budget_year: string; // e.g., "2025"
    dividend_ratio: string; // e.g., "0.05"
    total_dividend_amount: string; // e.g., "10000.00"
    status: 'Paid' | 'Pending'; // Enum for status
  }
  
  export interface DividendDistribution {
    id: number;
    dividend: Dividend; // Nested Dividend object
    user: User; // Assuming you have a User interface
    amount: string; // e.g., "500.00"
    created_at: string; // ISO date string
  }
  
  export interface User {
    id: number;
    username: string;
    // Add other relevant user fields if necessary
  }
  