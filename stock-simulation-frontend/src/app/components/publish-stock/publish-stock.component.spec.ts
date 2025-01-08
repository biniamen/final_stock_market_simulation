import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PublishStockComponent } from './publish-stock.component';

describe('PublishStockComponent', () => {
  let component: PublishStockComponent;
  let fixture: ComponentFixture<PublishStockComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ PublishStockComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PublishStockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
