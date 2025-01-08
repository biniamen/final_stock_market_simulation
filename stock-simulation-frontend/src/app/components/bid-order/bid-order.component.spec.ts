import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BidOrderComponent } from './bid-order.component';

describe('BidOrderComponent', () => {
  let component: BidOrderComponent;
  let fixture: ComponentFixture<BidOrderComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ BidOrderComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(BidOrderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
