import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DisclosureUploadComponent } from './disclosure-upload.component';

describe('DisclosureUploadComponent', () => {
  let component: DisclosureUploadComponent;
  let fixture: ComponentFixture<DisclosureUploadComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DisclosureUploadComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DisclosureUploadComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
