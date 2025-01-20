import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CompanyDividendsComponent } from './company-dividends.component';

describe('CompanyDividendsComponent', () => {
  let component: CompanyDividendsComponent;
  let fixture: ComponentFixture<CompanyDividendsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CompanyDividendsComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CompanyDividendsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
