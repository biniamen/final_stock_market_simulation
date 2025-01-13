import { TestBed } from '@angular/core/testing';

import { TransactionAuditService } from './transaction-audit.service';

describe('TransactionAuditService', () => {
  let service: TransactionAuditService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(TransactionAuditService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
