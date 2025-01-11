// src/app/models/transaction-audit.model.ts

export interface DetailsObject {
    buyer_id?: number;
    buyer_username?: string;
    price_per_share?: string;
    quantity?: number;
    remaining_quantity?: number;
    seller_id?: number;
    seller_username?: string;
    stock_id?: number;
    stock_symbol?: string;
    total_cost?: string;
    trade_type?: string;
    transaction_fee?: string;
    // Add other fields if necessary
  }
  
  export interface ITransactionAuditTrail {
    event_type: string;
    timestamp: string;
    details: string | DetailsObject;
    // Excluded fields: id, order, trade
  }
  